"""
Core file processing functionality for Workday Extend source files.
"""

import zipfile
import logging
from pathlib import Path
import tempfile
from typing import Dict, Set, Optional

from .config import FileProcessorConfig, DEFAULT_RELEVANT_EXTENSIONS
from .models import SourceFile

# Configure logging
logger = logging.getLogger(__name__)

class FileProcessingError(Exception):
    """Custom exception for file processing errors."""
    pass

class ZipProcessingError(FileProcessingError):
    """Exception raised when zip file processing fails."""
    pass

class FileReadError(FileProcessingError):
    """Exception raised when file reading fails."""
    pass

# Configuration constants (fallback values)
DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
DEFAULT_MAX_ZIP_SIZE = 500 * 1024 * 1024  # 500MB

class FileProcessor:
    """Handles file processing operations with practical resource management."""
    
    def __init__(
        self,
        config: Optional[FileProcessorConfig] = None,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
        max_zip_size: int = DEFAULT_MAX_ZIP_SIZE,
        relevant_extensions: Optional[Set[str]] = None,
        encoding: str = "utf-8"
    ):
        if config:
            self.config = config
            self.max_file_size = config.max_file_size
            self.max_zip_size = config.max_zip_size
            self.relevant_extensions = config.relevant_extensions
            self.encoding = config.encoding
        else:
            self.config = None
            self.max_file_size = max_file_size
            self.max_zip_size = max_zip_size
            self.relevant_extensions = relevant_extensions or DEFAULT_RELEVANT_EXTENSIONS
            self.encoding = encoding
        
        # Validate configuration
        if self.max_file_size <= 0 or self.max_zip_size <= 0:
            raise ValueError("Size limits must be positive")
        if not self.relevant_extensions:
            raise ValueError("At least one file extension must be specified")
    
    def _validate_zip_file(self, zip_path: Path) -> None:
        """Validate the zip file before processing."""
        if not zip_path.exists():
            raise FileNotFoundError(f"Zip file not found: {zip_path}")
        
        if not zip_path.is_file():
            raise FileProcessingError(f"Path is not a file: {zip_path}")
        
        # Check file size (practical limit)
        file_size = zip_path.stat().st_size
        if file_size > self.max_zip_size:
            raise ZipProcessingError(
                f"Zip file too large: {file_size} bytes (max: {self.max_zip_size} bytes)"
            )
        
        # Basic zip file integrity check
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Simple check that it's a valid zip file
                zip_ref.testzip()
        except zipfile.BadZipFile:
            raise ZipProcessingError(f"Invalid zip file: {zip_path}")
    
    def _read_file_safely(self, file_path: Path) -> Optional[str]:
        """Read a file safely with size checks."""
        try:
            # Check file size (practical limit)
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                logger.warning(f"File {file_path.name} too large ({file_size} bytes), skipping")
                return None
            
            # Read file content with fallback encodings
            content = self._read_with_fallback_encodings(file_path)
            if content:
                logger.debug(f"Successfully read file: {file_path.name} ({len(content)} characters)")
            return content
            
        except PermissionError as e:
            logger.warning(f"Permission denied reading {file_path.name}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error reading {file_path.name}: {e}")
            return None
    
    def _read_with_fallback_encodings(self, file_path: Path) -> Optional[str]:
        """Read file with fallback encodings if the primary encoding fails."""
        encodings_to_try = [self.encoding]
        
        # Add fallback encodings if config is available
        if self.config and hasattr(self.config, 'fallback_encodings'):
            encodings_to_try.extend(self.config.fallback_encodings)
        else:
            # Default fallback encodings
            encodings_to_try.extend(["latin-1", "cp1252"])
        
        for encoding in encodings_to_try:
            try:
                content = file_path.read_text(encoding=encoding)
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.debug(f"Failed to read {file_path.name} with encoding {encoding}: {e}")
                continue
        
        logger.warning(f"Failed to read {file_path.name} with any encoding")
        return None
    
    def process_zip_file(self, zip_path: Path) -> Dict[str, SourceFile]:
        """
        Extracts a zip file to a temporary directory and discovers all
        relevant Workday Extend source files.

        Args:
            zip_path: The path to the input .zip file.

        Returns:
            A dictionary mapping file paths (as strings) to SourceFile objects.
            
        Raises:
            FileProcessingError: For general file processing errors
            ZipProcessingError: For zip-specific errors
            FileNotFoundError: When zip file doesn't exist
        """
        logger.info(f"Starting processing of zip file: {zip_path}")
        
        # Validate input
        if not isinstance(zip_path, Path):
            zip_path = Path(zip_path)
        
        # Validate zip file
        self._validate_zip_file(zip_path)
        
        source_files = {}
        
        # Using a temporary directory is a best practice. It's automatically
        # cleaned up when the 'with' block is exited, even if errors occur.
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            logger.debug(f"Created temporary directory: {temp_dir}")

            # 1. --- Unzip the Archive ---
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_path)
                logger.info(f"Successfully extracted '{zip_path.name}' to temporary location")
            except zipfile.BadZipFile as e:
                raise ZipProcessingError(f"Invalid zip file '{zip_path.name}': {e}")
            except Exception as e:
                raise FileProcessingError(f"Failed to extract zip file '{zip_path.name}': {e}")

            # 2. --- Discover and Read Files ---
            logger.info("Searching for relevant source files...")
            
            # Path.rglob('*') is a powerful way to recursively search a directory.
            for file_path in temp_path.rglob('*'):
                # Check if the file has one of our target extensions.
                if file_path.is_file() and file_path.suffix in self.relevant_extensions:
                    logger.debug(f"Found relevant file: {file_path.name}")
                    
                    # Read the file content safely
                    content = self._read_file_safely(file_path)
                    if content is not None:
                        # We use a relative path as the key to keep it clean.
                        relative_path_str = str(file_path.relative_to(temp_path))
                        
                        try:
                            source_file = SourceFile(
                                path=file_path,
                                content=content,
                                size=len(content.encode(self.encoding))
                            )
                            source_files[relative_path_str] = source_file
                        except ValueError as e:
                            logger.warning(f"Invalid source file data for {file_path.name}: {e}")

            found_count = len(source_files)
            logger.info(f"Found {found_count} source file(s) to analyze")
            
            if found_count == 0:
                logger.warning("No relevant source files found in zip archive")
            
            return source_files
    
    def process_individual_files(self, file_paths: list[Path]) -> Dict[str, SourceFile]:
        """
        Process individual files (not in a ZIP).
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Dictionary mapping relative paths to SourceFile objects
            
        Raises:
            FileProcessingError: If file processing fails
        """
        source_files = {}
        
        for file_path in file_paths:
            # Validate file exists
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}, skipping")
                continue
            
            if not file_path.is_file():
                logger.warning(f"Path is not a file: {file_path}, skipping")
                continue
            
            # Check if file has relevant extension
            if file_path.suffix not in self.relevant_extensions:
                logger.warning(f"File {file_path.name} has unsupported extension {file_path.suffix}, skipping")
                continue
            
            # Read the file content safely
            content = self._read_file_safely(file_path)
            if content is not None:
                try:
                    source_file = SourceFile(
                        path=file_path,
                        content=content,
                        size=len(content.encode(self.encoding))
                    )
                    # Use the supplied path as the key so files with the same
                    # basename in different directories don't collide.
                    source_files[str(file_path)] = source_file
                    logger.info(f"Successfully processed: {file_path.name}")
                except ValueError as e:
                    logger.warning(f"Invalid source file data for {file_path.name}: {e}")
        
        logger.info(f"Processed {len(source_files)} file(s)")
        return source_files
    
    def process_directory(self, dir_path: Path) -> Dict[str, SourceFile]:
        """
        Process all relevant files in a directory (recursively).
        
        Args:
            dir_path: Directory path to scan
            
        Returns:
            Dictionary mapping relative paths to SourceFile objects
            
        Raises:
            FileProcessingError: If directory processing fails
        """
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if not dir_path.is_dir():
            raise FileProcessingError(f"Path is not a directory: {dir_path}")
        
        source_files = {}
        logger.info(f"Scanning directory: {dir_path}")
        
        # Recursively find all relevant files
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in self.relevant_extensions:
                logger.debug(f"Found relevant file: {file_path.name}")
                
                # Read the file content safely
                content = self._read_file_safely(file_path)
                if content is not None:
                    # Use relative path from the base directory
                    relative_path_str = str(file_path.relative_to(dir_path))
                    
                    try:
                        source_file = SourceFile(
                            path=file_path,
                            content=content,
                            size=len(content.encode(self.encoding))
                        )
                        source_files[relative_path_str] = source_file
                    except ValueError as e:
                        logger.warning(f"Invalid source file data for {file_path.name}: {e}")
        
        found_count = len(source_files)
        logger.info(f"Found {found_count} source file(s) in directory")
        
        if found_count == 0:
            logger.warning("No relevant source files found in directory")
        
        return source_files