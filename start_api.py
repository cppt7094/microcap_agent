"""
Project Tehama API - Server Startup Script
"""
import os
import sys
import logging
import traceback

# Setup logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("=" * 50)
        logger.info("Starting Project Tehama API")
        logger.info("=" * 50)

        # Log environment
        logger.info(f"Python version: {sys.version}")
        logger.info(f"PORT: {os.getenv('PORT', 'not set')}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Platform: {sys.platform}")

        # Import uvicorn
        logger.info("Importing uvicorn...")
        import uvicorn

        # Import app
        logger.info("Importing FastAPI app...")
        from api.main import app

        # Get port from environment (Railway sets this)
        port = int(os.getenv("PORT", 8000))
        logger.info(f"Will start server on port {port}")

        # Start server (disable reload in production)
        logger.info("Starting uvicorn server...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)

    except Exception as e:
        logger.error("=" * 50)
        logger.error("STARTUP FAILED!")
        logger.error("=" * 50)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 50)
        sys.exit(1)
