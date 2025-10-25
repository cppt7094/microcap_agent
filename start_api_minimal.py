"""
Minimal API Server - For Railway Deployment Debugging

This is a stripped-down version that tests basic functionality
without complex dependencies. Use this to isolate deployment issues.
"""
import os
import sys
import logging
from fastapi import FastAPI
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Project Tehama - Minimal Debug Version")


@app.get("/health")
def health():
    """Health check endpoint - verifies basic server functionality"""
    return {
        "status": "healthy",
        "port": os.getenv("PORT", "8000"),
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "platform": sys.platform,
        "env_vars": {
            "ANTHROPIC_API_KEY": "set" if os.getenv("ANTHROPIC_API_KEY") else "missing",
            "ALPACA_API_KEY": "set" if os.getenv("ALPACA_API_KEY") else "missing",
            "FMP_API_KEY": "set" if os.getenv("FMP_API_KEY") else "missing",
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "not set"),
        }
    }


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Project Tehama - Minimal Debug Version",
        "status": "operational",
        "note": "This is a minimal version for debugging deployment issues",
        "endpoints": {
            "/health": "Health check with environment info",
            "/": "This page"
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"=" * 50)
    logger.info(f"Starting MINIMAL server on port {port}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"=" * 50)

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
