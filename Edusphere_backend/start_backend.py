#!/usr/bin/env python3
"""
Startup script for the Edusphere Chatbot Backend
"""
import subprocess
import sys
import os

def main():
    print("Starting Edusphere Chatbot Backend...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ Error: app.py not found. Please run this script from the Edusphere_backend directory.")
        sys.exit(1)
    
    # Check if virtual environment exists
    if not os.path.exists(".venv"):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
    
    # Determine the correct pip and python paths
    if sys.platform.startswith('win'):
        pip_path = ".venv\\Scripts\\pip"
        python_path = ".venv\\Scripts\\python"
        uvicorn_path = ".venv\\Scripts\\uvicorn.exe"
    else:
        pip_path = ".venv/bin/pip"
        python_path = ".venv/bin/python"
        uvicorn_path = ".venv/bin/uvicorn"
    
    # Install dependencies
    print("Installing dependencies...")
    try:
        subprocess.run([pip_path, "install", "-r", "requirements_simple.txt"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ Warning: Could not install from requirements_simple.txt, trying original requirements.txt...")
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    
    # Start the FastAPI server using uvicorn
    print("Starting FastAPI server on http://localhost:5001...")
    print("API Documentation will be available at http://localhost:5001/docs")
    print("=" * 50)
    
    try:
        subprocess.run([uvicorn_path, "app:app", "--host", "0.0.0.0", "--port", "5001", "--reload"], check=True)
    except KeyboardInterrupt:
        print("\nBackend server stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

