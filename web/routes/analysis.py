"""
Analysis routes for Arcane Auditor.

Handles file uploads, job status, and result downloads.
"""

import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse

from pydantic import BaseModel
from typing import Optional

from web.services.jobs import AnalysisJob, analysis_jobs, job_lock, run_analysis_background, cleanup_old_jobs
from web.services.config_loader import get_dynamic_config_info

router = APIRouter()

# Configuration constants
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB default limit
CHUNK_SIZE = 8192  # 8KB chunks for streaming


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    config: Optional[str] = None


@router.post("/api/upload")
async def upload_file(
    files: list[UploadFile] = File(...), 
    config: str = Form("default")
):
    """
    Upload file(s) for analysis.
    
    Supports:
    - Single ZIP file: Complete application archive
    - Multiple individual files: .pmd, .pod, .amd, .smd, .script files
    """
    
    # Validate we have files
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Determine if this is a ZIP upload or individual files
    is_zip_upload = len(files) == 1 and files[0].filename.lower().endswith('.zip')
    
    # Validate configuration
    config_info = get_dynamic_config_info()
    if config not in config_info:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {config}")
    
    # Get the actual config path from the selected config key
    selected_config_info = config_info[config]
    actual_config_path = selected_config_info["path"]
    config_source = selected_config_info.get("source", "built-in")  # Get the source (presets, teams, personal)
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file(s)
    uploads_dir = Path(__file__).parent.parent / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    
    try:
        if is_zip_upload:
            # ZIP file mode
            file = files[0]
            
            # Validate file size
            if file.size and file.size > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
            
            zip_path = uploads_dir / f"{job_id}.zip"
            
            # Stream file to disk
            with open(zip_path, "wb") as buffer:
                while chunk := await file.read(CHUNK_SIZE):
                    buffer.write(chunk)
            
            # Create analysis job for ZIP
            job = AnalysisJob(job_id, zip_path, actual_config_path, config_source)
            job.is_zip = True
        
        else:
            # Individual files mode
            saved_files = []
            
            for file in files:
                # Validate file extension
                valid_extensions = ['.pmd', '.pod', '.amd', '.smd', '.script', '.wqlquery', '.orchestration', '.suborchestration']
                if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
                    raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}. Only {', '.join(valid_extensions)} files are allowed.")
                
                # Validate file size
                if file.size and file.size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail=f"File {file.filename} too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
                
                # Save file
                file_path = uploads_dir / f"{job_id}_{file.filename}"
                with open(file_path, "wb") as buffer:
                    while chunk := await file.read(CHUNK_SIZE):
                        buffer.write(chunk)
                
                saved_files.append(file_path)
            
            # Create analysis job for individual files
            job = AnalysisJob(job_id, None, actual_config_path, config_source)
            job.is_zip = False
            job.individual_files = saved_files
        
        with job_lock:
            analysis_jobs[job_id] = job
        
        # Start background analysis
        job.thread = threading.Thread(target=run_analysis_background, args=(job,))
        job.thread.daemon = True
        job.thread.start()
        
        # Cleanup old jobs
        cleanup_old_jobs()
        
        return {"job_id": job_id, "status": "queued", "config": actual_config_path}
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up files if upload failed
        if is_zip_upload and 'zip_path' in locals() and zip_path.exists():
            zip_path.unlink()
        elif 'saved_files' in locals():
            for file_path in saved_files:
                if file_path.exists():
                    file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/api/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of an analysis job."""
    with job_lock:
        if job_id not in analysis_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = analysis_jobs[job_id]
        return JobStatusResponse(**job.to_dict())


@router.get("/api/download/{job_id}")
async def download_excel(job_id: str):
    """Download analysis results as Excel file."""
    with job_lock:
        if job_id not in analysis_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = analysis_jobs[job_id]
        
        if job.status != "completed":
            raise HTTPException(status_code=400, detail="Analysis not completed")
        
        if not job.result:
            raise HTTPException(status_code=500, detail="No results available")
        
        try:
            # Use shared OutputFormatter logic for Excel generation
            from output.formatter import OutputFormatter, OutputFormat
            from datetime import datetime
            
            # Convert web service findings to CLI format for compatibility
            findings = []
            for finding_data in job.result["findings"]:
                # Create a simple Finding-like object for compatibility
                class WebFinding:
                    def __init__(self, data):
                        self.rule_id = data["rule_id"]
                        self.severity = data["severity"]
                        self.line = data["line"]
                        self.message = data["message"]
                        self.file_path = data["file_path"]
                
                findings.append(WebFinding(finding_data))
            
            # Create a mock ProjectContext with context information if available
            class MockProjectContext:
                def __init__(self, context_data):
                    self.analysis_context = None
                    if context_data:
                        # Recreate AnalysisContext from stored data
                        from file_processing.context_tracker import AnalysisContext
                        self.analysis_context = AnalysisContext(
                            analysis_type=context_data.get("analysis_type", "unknown"),
                            files_analyzed=context_data.get("files_analyzed", []),
                            files_present=set(context_data.get("files_present", []))
                        )
            
            # Use OutputFormatter to generate Excel with context tab
            formatter = OutputFormatter(OutputFormat.EXCEL)
            total_files = len(set(finding.file_path for finding in findings if finding.file_path))
            total_rules = job.result["summary"]["rules_executed"]
            context = MockProjectContext(job.result.get("context"))
            config_name = job.result.get("config_name")
            config_source = job.result.get("config_source")
            
            # Read the single tab export preference
            from utils.preferences_manager import get_excel_single_tab
            single_tab = get_excel_single_tab()
            
            excel_file_path = formatter.format_results(findings, total_files, total_rules, context, config_name, config_source, single_tab)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y-%m-%d")
            filename = f"arcane-auditor-results-{timestamp}.xlsx"
            
            return FileResponse(
                path=excel_file_path,
                filename=filename,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")


