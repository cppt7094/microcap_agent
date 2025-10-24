"""
Project Tehama API - Automatic Dependency Installation
"""
import subprocess
import sys
import codecs

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def main():
    print("\n" + "="*60)
    print("Project Tehama API - Dependency Installation")
    print("="*60 + "\n")

    packages = ["fastapi", "uvicorn[standard]", "pydantic"]

    print("Installing packages:", ", ".join(packages))
    print("-" * 60)

    for package in packages:
        print(f"\nInstalling {package}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print(f"✓ {package} installed successfully")
            else:
                print(f"✗ Error installing {package}")
                print(result.stderr)
        except Exception as e:
            print(f"✗ Exception installing {package}: {e}")

    # Test imports
    print("\n" + "="*60)
    print("Testing imports...")
    print("="*60)

    try:
        import fastapi
        print(f"✓ FastAPI version: {fastapi.__version__}")

        import uvicorn
        print(f"✓ Uvicorn imported successfully")

        import pydantic
        print(f"✓ Pydantic version: {pydantic.__version__}")

        print("\n✅ All dependencies installed and working!\n")

        # Show next steps
        print("="*60)
        print("NEXT STEPS")
        print("="*60)
        print("\n1. Start the API server:")
        print("   python start_api.py")
        print("\n2. Test the endpoints:")
        print("   python test_api_endpoints.py")
        print("\n3. Or use curl:")
        print("   curl http://localhost:8000/api/portfolio")
        print("\n4. Interactive docs:")
        print("   http://localhost:8000/docs")
        print("\n" + "="*60 + "\n")

    except ImportError as e:
        print(f"\n✗ Import test failed: {e}")
        print("\nPlease install manually:")
        print("  pip install fastapi uvicorn pydantic")

if __name__ == "__main__":
    main()
