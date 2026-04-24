"""
PE Memory OS - Packaged Application Entry Point
This module serves the built frontend static files and starts the FastAPI server.
"""

import os
import sys
from pathlib import Path

# Determine if we're running from a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Running in normal Python environment
    BASE_DIR = Path(__file__).parent.parent

# Set up paths for the application
STATIC_DIR = BASE_DIR / "build"
WORKSPACE_DIR = Path.home() / "Library/Application Support/PE Memory OS"
DATA_DIR = WORKSPACE_DIR / "data"

# Ensure workspace directories exist
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Set environment variables for the backend
os.environ.setdefault("WORKSPACE_ROOT", str(WORKSPACE_DIR))
os.environ.setdefault("SQLITE_PATH", str(DATA_DIR / "app.db"))
os.environ.setdefault("DUCKDB_PATH", str(DATA_DIR / "analytics.duckdb"))
os.environ.setdefault("QDRANT_PATH", str(DATA_DIR / "qdrant"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import the main FastAPI app
from backend.main import app as fastapi_app

@fastapi_app.get("/debug_info")
def get_debug_info():
    import sys
    return {
        "__file__": __file__,
        "STATIC_DIR": str(STATIC_DIR),
        "STATIC_EXISTS": STATIC_DIR.exists(),
        "STATIC_INDEX_EXISTS": (STATIC_DIR / "index.html").exists(),
        "sys.path": sys.path,
        "is_frozen": getattr(sys, 'frozen', False),
    }

if STATIC_DIR.exists():
    fastapi_app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @fastapi_app.get("/")
    async def serve_index():
        return FileResponse(str(STATIC_DIR / "index.html"))

    @fastapi_app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Serve index.html for all non-API routes (SPA behavior)
        if not full_path.startswith("api/") and not full_path.startswith("docs") and not full_path.startswith("config/"):
            index_file = STATIC_DIR / "index.html"
            if index_file.exists():
                return FileResponse(str(index_file))
        return {"detail": "Not Found"}

# Export the app for uvicorn
app = fastapi_app

def main():
    """Entry point for the packaged application."""
    import uvicorn
    import webbrowser
    import threading
    import time

    host = "127.0.0.1"
    port = 8000

    def open_browser():
        """Open browser after a short delay to let server start."""
        time.sleep(2)
        webbrowser.open(f"http://{host}:{port}")

    # Open browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Start the server
    uvicorn.run(
        "backend.app:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
