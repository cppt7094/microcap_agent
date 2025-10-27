import sys
import os

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)

print("=" * 80, flush=True)
print("RAILWAY STARTUP - VERBOSE MODE", flush=True)
print("=" * 80, flush=True)
print(f"Python: {sys.version}", flush=True)
print(f"CWD: {os.getcwd()}", flush=True)
print(f"PORT: {os.getenv('PORT', 'NOT SET')}", flush=True)
print(f"RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', 'NOT SET')}", flush=True)
print("=" * 80, flush=True)

try:
    print("Step 1: Importing uvicorn...", flush=True)
    import uvicorn
    print("✓ uvicorn imported", flush=True)

    print("Step 2: Importing FastAPI...", flush=True)
    from fastapi import FastAPI
    print("✓ FastAPI imported", flush=True)

    print("Step 3: Importing api.main...", flush=True)
    from api.main import app
    print("✓ api.main imported", flush=True)

    port = int(os.getenv("PORT", 8000))
    print(f"Step 4: Starting uvicorn on port {port}...", flush=True)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="debug"
    )

except ImportError as e:
    print("=" * 80, flush=True)
    print("IMPORT ERROR!", flush=True)
    print("=" * 80, flush=True)
    print(f"Failed to import: {e}", flush=True)
    import traceback
    print(traceback.format_exc(), flush=True)
    sys.exit(1)

except Exception as e:
    print("=" * 80, flush=True)
    print("STARTUP ERROR!", flush=True)
    print("=" * 80, flush=True)
    print(f"Error: {e}", flush=True)
    import traceback
    print(traceback.format_exc(), flush=True)
    sys.exit(1)
