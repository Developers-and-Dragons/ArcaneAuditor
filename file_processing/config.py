"""
Configuration settings for file processing operations.
Simplified for internal use with practical resource management.
"""
from typing import Set
from pathlib import Path

# File size limits (practical limits for internal use)
DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
DEFAULT_MAX_ZIP_SIZE = 500 * 1024 * 1024  # 500MB

# Supported file extensions for Workday Extend
DEFAULT_RELEVANT_EXTENSIONS = {".pod", ".pmd", ".script", ".amd", ".smd", ".wqlquery", ".orchestration", ".suborchestration"}

# Encoding settings
DEFAULT_ENCODING = "utf-8"
FALLBACK_ENCODINGS = ["utf-8", "latin-1", "cp1252"]

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Performance settings
CHUNK_SIZE = 8192  # 8KB chunks for large file processing
MAX_CONCURRENT_FILES = 10

class FileProcessorConfig:
    """Configuration class for file processing operations."""
    
    def __init__(
        self,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
        max_zip_size: int = DEFAULT_MAX_ZIP_SIZE,
        relevant_extensions: Set[str] = None,
        encoding: str = DEFAULT_ENCODING,
        log_level: str = LOG_LEVEL,
        chunk_size: int = CHUNK_SIZE,
        max_concurrent_files: int = MAX_CONCURRENT_FILES,
        fallback_encodings: Set[str] = None
    ):
        self.max_file_size = max_file_size
        self.max_zip_size = max_zip_size
        self.relevant_extensions = relevant_extensions or DEFAULT_RELEVANT_EXTENSIONS.copy()
        self.encoding = encoding
        self.log_level = log_level
        self.chunk_size = chunk_size
        self.max_concurrent_files = max_concurrent_files
        self.fallback_encodings = fallback_encodings or set(FALLBACK_ENCODINGS)
        
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if self.max_file_size <= 0:
            raise ValueError("max_file_size must be positive")
        if self.max_zip_size <= 0:
            raise ValueError("max_zip_size must be positive")
        if not self.relevant_extensions:
            raise ValueError("At least one file extension must be specified")
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.max_concurrent_files <= 0:
            raise ValueError("max_concurrent_files must be positive")
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "max_file_size": self.max_file_size,
            "max_zip_size": self.max_zip_size,
            "relevant_extensions": list(self.relevant_extensions),
            "encoding": self.encoding,
            "log_level": self.log_level,
            "chunk_size": self.chunk_size,
            "max_concurrent_files": self.max_concurrent_files,
            "fallback_encodings": list(self.fallback_encodings)
        }
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'FileProcessorConfig':
        """Create configuration from dictionary."""
        return cls(**config_dict)
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'FileProcessorConfig':
        """Load configuration from JSON file."""
        import json
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)
    
    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to JSON file."""
        import json
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
