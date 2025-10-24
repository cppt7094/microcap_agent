"""
Project Tehama API - Installation and Test Script
This script will help you install dependencies and test the API
"""
import subprocess
import sys
import time
import json
import codecs

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def install_dependencies():
    """Install required FastAPI dependencies"""
    print("📦 Installing FastAPI dependencies...")
    print("-" * 50)

    packages = ["fastapi", "uvicorn[standard]", "pydantic"]

    for package in packages:
        print(f"\nInstalling {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error installing {package}: {e}")
            return False

    print("\n✅ All dependencies installed successfully!\n")
    return True

def test_imports():
    """Test if all imports work"""
    print("🔍 Testing imports...")
    print("-" * 50)

    try:
        import fastapi
        print(f"✓ FastAPI version: {fastapi.__version__}")

        import uvicorn
        print(f"✓ Uvicorn imported successfully")

        import pydantic
        print(f"✓ Pydantic version: {pydantic.__version__}")

        print("\n✅ All imports successful!\n")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def start_server_instructions():
    """Display instructions for starting the server"""
    print("\n" + "="*60)
    print("🚀 NEXT STEPS - Starting the API Server")
    print("="*60)
    print("\nOption 1: Using the start script")
    print("  python start_api.py")
    print("\nOption 2: Using uvicorn directly")
    print("  uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n" + "="*60)
    print("🧪 TESTING ENDPOINTS")
    print("="*60)
    print("\nOnce the server is running, test these endpoints:")
    print("\n1. Health Check:")
    print("   curl http://localhost:8000/health")
    print("\n2. Portfolio:")
    print("   curl http://localhost:8000/api/portfolio")
    print("\n3. Recommendations:")
    print("   curl http://localhost:8000/api/recommendations")
    print("\n4. Agent Status:")
    print("   curl http://localhost:8000/api/agents/status")
    print("\n5. Alerts:")
    print("   curl http://localhost:8000/api/alerts")
    print("\n6. Interactive Docs:")
    print("   Open browser: http://localhost:8000/docs")
    print("\n" + "="*60 + "\n")

def main():
    print("\n" + "="*60)
    print("🚀 Project Tehama API - Setup & Installation")
    print("="*60 + "\n")

    # Step 1: Install dependencies
    choice = input("Install FastAPI dependencies? (y/n): ").lower()
    if choice == 'y':
        if not install_dependencies():
            print("\n❌ Installation failed. Please install manually:")
            print("   pip install fastapi uvicorn pydantic")
            sys.exit(1)

    # Step 2: Test imports
    if not test_imports():
        print("\n❌ Import test failed. Please check installation.")
        sys.exit(1)

    # Step 3: Show instructions
    start_server_instructions()

if __name__ == "__main__":
    main()
