#!/usr/bin/env python3
"""
FastAPI server for the HTML frontend of Arcane Auditor.
This serves the simple HTML/JavaScript interface with FastAPI backend.
"""

from contextlib import asynccontextmanager
import sys
import threading
import time
import asyncio

from pathlib import Path
import webbrowser
import json
import shutil
import argparse

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# FastAPI imports
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles as StarletteStaticFiles
import uvicorn

# Arcane paths for path resolution
from utils.arcane_paths import (
    resource_path,
    ensure_sample_rule_config,
    is_frozen,
    user_root,
)

# Import routers
from web.routes import configs, analysis, health, preferences

# Import services
from web.services.jobs import cleanup_orphaned_files, cleanup_old_jobs

# Import version from centralized module
from __version__ import __version__


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Clean up orphaned files on server startup."""
    cleanup_orphaned_files()
    
    # Start periodic cleanup task
    asyncio.create_task(periodic_cleanup())
    yield


async def periodic_cleanup():
    """Run cleanup every 5 minutes."""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        cleanup_orphaned_files()
        cleanup_old_jobs()


# Initialize FastAPI app
app = FastAPI(
    title="Arcane Auditor API",
    description="Workday Extend Code Review Tool API",
    version=__version__,
    lifespan=lifespan
)

# Desktop shell enables local directory analysis; default off for standalone web server.
app.state.allow_directory_analysis = False


# Mount static files at /static to avoid conflicts with API routes
if is_frozen():
    static_dir = Path(resource_path("web/frontend"))
else:
    static_dir = Path(__file__).parent / "frontend"


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(configs.router)
app.include_router(analysis.router)
app.include_router(health.router)
app.include_router(preferences.router)


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main HTML page."""
    index_path = static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index file not found")
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add cache-busting headers for development
    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Custom static file handler with cache-busting headers
class NoCacheStaticFiles(StarletteStaticFiles):
    """Static file handler that adds cache-busting headers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add cache-busting headers to all static file responses
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    # Add cache-busting headers
                    headers = list(message.get("headers", []))
                    # Remove existing cache headers if present
                    headers = [(k, v) for k, v in headers if k.lower() not in (b"cache-control", b"pragma", b"expires")]
                    # Add new cache-busting headers
                    headers.extend([
                        (b"cache-control", b"no-cache, no-store, must-revalidate"),
                        (b"pragma", b"no-cache"),
                        (b"expires", b"0")
                    ])
                    message["headers"] = headers
                await send(message)
            await super().__call__(scope, receive, send_wrapper)
        else:
            await super().__call__(scope, receive, send)

# Mount static files at /static to avoid conflicts with API routes
app.mount("/static", NoCacheStaticFiles(directory=str(static_dir)), name="static")


def load_web_config(cli_args=None):
    """
    Load the web service configuration, optionally overridden by CLI args.
    Precedence: CLI args > config file > built-in defaults.
    """
    defaults = {
        "host": "127.0.0.1",
        "port": 8080,
        "open_browser": True,
        "log_level": "info"
    }

    # Determine config path based on mode
    if is_frozen():
        user_cfg = Path(user_root()) / "config" / "web" / "web_service_config.json"
        bundled_sample = Path(resource_path("config/web/web_service_config.json.sample"))

        # Copy default config to user AppData if missing
        if not user_cfg.exists():
            user_cfg.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(bundled_sample, user_cfg)
                print(f"Created new user web config at {user_cfg}")
            except Exception as e:
                print(f"Failed to copy bundled web config: {e}")

        cfg_path = user_cfg
    else:
        repo_root = Path(__file__).resolve().parent.parent
        cfg_path = repo_root / "config" / "web" / "web_service_config.json"

    # Start from defaults, then overlay config file if it exists
    config = defaults.copy()
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                config.update(json.load(f))
            print(f"Using web config: {cfg_path}")
        except Exception as e:
            print(f"Could not read {cfg_path} ({e}); using defaults.")

    # Overlay CLI args if provided
    if cli_args:
        if cli_args.host:
            config["host"] = cli_args.host
        if cli_args.port:
            config["port"] = cli_args.port
        if cli_args.open_browser:
            config["open_browser"] = True
        elif cli_args.no_browser:
            config["open_browser"] = False
        if cli_args.log_level:
            config["log_level"] = cli_args.log_level

    return config


def parse_args():
    parser = argparse.ArgumentParser(description="Arcane Auditor Web Service")

    parser.add_argument("--host", type=str, help="Host to bind the server to (default from config or 127.0.0.1)")
    parser.add_argument("--port", type=int, help="Port to run the server on (default from config or 8080)")
    parser.add_argument("--open-browser", action="store_true", help="Open browser automatically on startup")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically on startup")
    parser.add_argument("--log-level", type=str, choices=["info", "debug", "warning", "error"], help="Set logging verbosity")

    return parser.parse_args()


def main():
    """Main function to run the server."""
    args = parse_args()
    cfg = load_web_config(args)

    host = cfg.get("host", "127.0.0.1")
    port = cfg.get("port", 8080)
    open_browser = cfg.get("open_browser", True)
  
    if open_browser:
        # Open browser after a short delay
        def open_browser():
            time.sleep(1)
            webbrowser.open(f"http://{host}:{port}")
        
        threading.Thread(target=open_browser, daemon=True).start()
    
    print(f"Starting Arcane Auditor FastAPI server on http://{host}:{port}")
    print("Press Ctrl+C to stop the server")

    # Ensure sample rule config is seeded
    ensure_sample_rule_config()
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
