#!/usr/bin/env python3
"""
Script to run the Knowledge Base Search Engine frontend
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    # Check if node_modules exists
    if not Path("node_modules").exists():
        print("Installing npm dependencies...")
        subprocess.run(["npm", "install"])
    
    # Start the development server
    print("Starting React development server...")
    subprocess.run(["npm", "start"])

if __name__ == "__main__":
    main()

