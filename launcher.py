#!/usr/bin/env python3
"""
PE Memory OS - macOS App Launcher
Lightweight launcher that starts the backend and opens the browser.
"""

import os
import sys
import subprocess
import time
import webbrowser
import signal
import argparse
from pathlib import Path
import os
sys.stdout = sys.stderr = open(os.path.expanduser('~/Desktop/launcher.log'), 'w', buffering=1)

# Configuration
APP_NAME = "PE Memory OS"
DEFAULT_PORT = 8000
DEFAULT_HOST = "127.0.0.1"

def get_project_root() -> Path:
    """Get the project root directory."""
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        exe_path = Path(sys.executable).resolve()
        if "Contents/MacOS" in str(exe_path):
            return exe_path.parents[4]
        return exe_path.parents[1]
    else:
        # Running in normal Python environment
        return Path(__file__).parent.resolve()

def check_dependencies() -> bool:
    """Check if Python dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import qdrant_client
        import docling
        return True
    except ImportError as e:
        return False

def setup_environment(project_root: Path) -> dict:
    """Set up environment variables and workspace."""
    # Create workspace in user's Application Support
    workspace_dir = Path.home() / "Library/Application Support/PE Memory OS"
    data_dir = workspace_dir / "data"

    workspace_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["WORKSPACE_ROOT"] = str(workspace_dir)
    env["DATABASE_URL"] = f"sqlite:///{data_dir / 'app.db'}"
    env["DUCKDB_PATH"] = str(data_dir / "analytics.duckdb")
    env["QDRANT_PATH"] = str(data_dir / "qdrant")

    return env

def start_server(project_root: Path, env: dict, host: str, port: int) -> subprocess.Popen:
    """Start the FastAPI backend server."""
    backend_dir = project_root / "backend"

    # Use python from virtual environment if available
    venv_python = project_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        python_exe = str(venv_python)
    else:
        msg = f"Could not find local python virtual environment at:\n{venv_python}\n\nPlease run 'python -m venv .venv' first."
        print(f"Error: {msg}")
        if sys.platform == "darwin" and getattr(sys, 'frozen', False):
            subprocess.run(["osascript", "-e", f'display alert "PE Memory OS Launcher Error" message "{msg}" as critical'])
        sys.exit(1)

    cmd = [
        python_exe, "-m", "uvicorn",
        "backend.app:app",
        "--host", host,
        "--port", str(port)
    ]

    process = subprocess.Popen(
        cmd,
        cwd=str(project_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return process

def wait_for_server(host: str, port: int, timeout: int = 30) -> bool:
    """Wait for the server to be ready."""
    import urllib.request
    import urllib.error

    url = f"http://{host}:{port}/health"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError):
            time.sleep(0.5)

    return False

def open_browser(host: str, port: int):
    """Open the browser to the app."""
    url = f"http://{host}:{port}"
    if sys.platform == "darwin":
        import subprocess
        subprocess.run(["open", url])
    else:
        webbrowser.open(url)

def main():
    parser = argparse.ArgumentParser(description=f'{APP_NAME} Launcher')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Port to run the server on')
    parser.add_argument('--host', type=str, default=DEFAULT_HOST, help='Host to bind the server to')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    args = parser.parse_args()

    project_root = get_project_root()

    # Check if running from source or bundled
    is_bundled = getattr(sys, 'frozen', False)

    if not is_bundled:
        # Running from source - check dependencies
        if not check_dependencies():
            print("Error: Python dependencies not installed.")
            print(f"Please run: cd '{project_root}' && pip install -r requirements.txt")
            sys.exit(1)

    # Set up environment
    env = setup_environment(project_root)

    print(f"Starting {APP_NAME}...")
    print(f"Workspace: {env['WORKSPACE_ROOT']}")

    # Start the server
    try:
        server_process = start_server(project_root, env, args.host, args.port)

        print(f"Waiting for server to start on {args.host}:{args.port}...")

        # Wait for server with timeout
        if not wait_for_server(args.host, args.port, timeout=30):
            print("Error: Server failed to start within 30 seconds")
            server_process.terminate()
            sys.exit(1)

        print(f"Server started successfully!")

        # Open browser
        if not args.no_browser:
            print(f"Opening browser...")
            open_browser(args.host, args.port)

        print(f"\n{APP_NAME} is running at http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop the server\n")

        # Wait for server to finish
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\nShutting down...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
