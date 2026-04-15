"""
Job management service for Arcane Auditor.

Handles analysis job creation, execution, and cleanup.
"""

import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional

# Global job management for async analysis
analysis_jobs: Dict[str, 'AnalysisJob'] = {}
job_lock = threading.Lock()


class AnalysisJob:
    """Represents an analysis job with status tracking."""
    def __init__(self, job_id: str, zip_path: Path = None, config: str = "default", config_source: str = "built-in"):
        self.job_id = job_id
        self.zip_path = zip_path
        self.config = config
        self.config_source = config_source  # Track if config is built-in, personal, or team
        self.status = "queued"  # queued, running, completed, failed
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.thread = None
        self.is_zip = True  # True for ZIP files, False for individual files or directory
        self.is_directory = False  # True when analyzing a local folder (desktop)
        self.directory_path: Optional[Path] = None
        self.individual_files = []  # List of Path objects for individual files
    
    def to_dict(self):
        """Convert job to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "config": self.config
        }


def cleanup_orphaned_files():
    """Clean up orphaned files from previous server runs."""
    uploads_dir = Path(__file__).parent.parent / "uploads"
    if uploads_dir.exists():
        current_time = time.time()
        files_found = 0
        files_deleted = 0
        
        for file_path in uploads_dir.glob("*.zip"):
            files_found += 1
            file_age = current_time - file_path.stat().st_mtime
            # Delete files older than 1 hour
            if file_age > 3600:
                try:
                    file_path.unlink()
                    files_deleted += 1
                    print(f"Cleaned up orphaned file: {file_path.name} (age: {file_age/60:.1f} minutes)")
                except Exception as e:
                    print(f"Failed to clean up {file_path.name}: {e}")
            else:
                print(f"Keeping file: {file_path.name} (age: {file_age/60:.1f} minutes)")
        
        print(f"Cleanup summary: {files_found} files found, {files_deleted} files deleted")


def cleanup_old_jobs():
    """Remove completed/failed jobs older than 1 hour."""
    current_time = time.time()
    with job_lock:
        jobs_to_remove = []
        for job_id, job in analysis_jobs.items():
            if job.status in ["completed", "failed"] and job.end_time:
                if current_time - job.end_time > 3600:  # 1 hour
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            job = analysis_jobs.pop(job_id)
            # Clean up any remaining temporary files (never delete user directory sources)
            if getattr(job, "is_directory", False):
                continue
            if job.is_zip and job.zip_path and job.zip_path.exists():
                job.zip_path.unlink()
                print(f"Cleaned up remaining ZIP file: {job.zip_path.name}")
            elif not job.is_zip and job.individual_files:
                for file_path in job.individual_files:
                    if file_path.exists():
                        file_path.unlink()
                        print(f"Cleaned up remaining file: {file_path.name}")


def run_analysis_background(job: AnalysisJob):
    """Run analysis in background thread."""
    try:
        job.status = "running"
        job.start_time = time.time()
        
        # Import analysis modules here to avoid import issues
        from file_processing.processor import FileProcessor
        from parser.app_parser import ModelParser
        from parser.rules_engine import RulesEngine
        from parser.config_manager import ConfigurationManager
            
        # Process files based on job type
        file_processing_start = time.time()
        processor = FileProcessor()
        
        if getattr(job, "is_directory", False) and job.directory_path:
            source_files_map = processor.process_directory(job.directory_path)
        elif job.is_zip:
            # ZIP file mode
            source_files_map = processor.process_zip_file(job.zip_path)
            
            # Delete ZIP file immediately after successful processing
            if job.zip_path and job.zip_path.exists():
                job.zip_path.unlink()
                print(f"Deleted processed ZIP file: {job.zip_path.name}")
        else:
            # Individual files mode
            source_files_map = processor.process_individual_files(job.individual_files)
            
            # Delete individual files immediately after successful processing
            for file_path in job.individual_files:
                if file_path.exists():
                    file_path.unlink()
                    print(f"Deleted processed file: {file_path.name}")
        
        file_processing_time = time.time() - file_processing_start
        
        if not source_files_map:
            job.error = "No valid source files found"
            job.status = "failed"
            job.end_time = time.time()
            return
            
        # Create project context
        parsing_start = time.time()
        parser = ModelParser()
        context = parser.parse_files(source_files_map)
        parsing_time = time.time() - parsing_start
        
        # Run analysis with specified configuration
        config_start = time.time()
        # Use project root as base path for configuration loading
        # __file__ is in web/services/, so go up 2 levels to get project root
        project_root = Path(__file__).parent.parent.parent
        config_manager = ConfigurationManager(project_root)
        config = config_manager.load_config(job.config)
        rules_engine = RulesEngine(config)
        config_time = time.time() - config_start
        
        analysis_start = time.time()
        findings = rules_engine.run(context)
        analysis_time = time.time() - analysis_start
        
        # Log performance metrics
        total_time = time.time() - job.start_time
        print(f"Performance metrics for job {job.job_id}:")
        print(f"  File processing: {file_processing_time:.2f}s")
        print(f"  Parsing: {parsing_time:.2f}s")
        print(f"  Config loading: {config_time:.2f}s")
        print(f"  Analysis: {analysis_time:.2f}s")
        print(f"  Total: {total_time:.2f}s")
            
        # Convert findings to serializable format
        result = {
            "findings": [
                {
                    "rule_id": finding.rule_id,
                    "severity": finding.severity,
                    "message": finding.message,
                    "file_path": finding.file_path,
                    "line": finding.line
                    }
                    for finding in findings
            ],
            "summary": {
                "total_findings": len(findings),
                "rules_executed": len(rules_engine.rules),
                "by_severity": {
                    "action": len([f for f in findings if f.severity == "ACTION"]),
                    "advice": len([f for f in findings if f.severity == "ADVICE"])
                }
            },
            "config_name": job.config,  # Add config name to result
            "config_source": job.config_source  # Add config source to result
        }
        
        # Add context awareness information if available
        if context.analysis_context:
            result["context"] = context.analysis_context.to_dict()
        
        job.result = result
        job.status = "completed"
        job.end_time = time.time()
        
    except Exception as e:
        job.error = str(e)
        job.status = "failed"
        job.end_time = time.time()
        print(f"Analysis failed: {e}", file=sys.stderr)

