#!/usr/bin/env python3
"""
Launcher for the PixelPilot API Server.
This file should be run to start the FastAPI server.
"""

import subprocess
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    # Run uvicorn with the app
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.server:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    print("Starting PixelPilot API Server...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Server stopped by user")