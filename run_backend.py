#!/usr/bin/env python3
"""
Script to run the Knowledge Base Search Engine backend
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Check if virtual environment exists
    venv_path = Path("../venv")
    if venv_path.exists():
        if sys.platform == "win32":
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            python_path = venv_path / "bin" / "python"
        
        if python_path.exists():
            print("Using virtual environment...")
            subprocess.run([str(python_path), "main.py"])
        else:
            print("Virtual environment found but Python executable not found.")
            print("Please recreate the virtual environment.")
            sys.exit(1)
    else:
        print("Virtual environment not found. Using system Python...")
        subprocess.run([sys.executable, "main.py"])

if __name__ == "__main__":
    main()

