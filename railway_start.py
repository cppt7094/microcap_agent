"""
Railway startup wrapper with comprehensive error logging
"""
import sys
import os
import logging
import traceback

# Setup logging to stdout immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("=" * 60)
        logger.info("RAILWAY STARTUP - Project Tehama")
        logger.info("=" * 60)

        # Log environment
        logger.info(f"Python: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"PORT: {os.environ.get('PORT', 'NOT SET')}")
        logger.info(f"RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT', 'NOT SET')}")

        # Check API keys (without revealing them)
        logger.info("Checking API keys...")
        for key in ['ANTHROPIC_API_KEY', 'ALPACA_API_KEY', 'ALPACA_SECRET_KEY', 'FMP_API_KEY']:
            value = os.environ.get(key)
            if value:
                logger.info(f"  ✓ {key}: Set ({len(value)} chars)")
            else:
                logger.error(f"  ✗ {key}: MISSING!")

        # Check if /tmp is writable
        logger.info("Checking filesystem...")
        try:
            test_file = "/tmp/railway_test.txt"
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            logger.info("  ✓ /tmp is writable")
        except Exception as e:
            logger.error(f"  ✗ /tmp write test failed: {e}")

        # Import uvicorn
        logger.info("Importing uvicorn...")
        import uvicorn
        logger.info("  ✓ uvicorn imported")

        # Import FastAPI app
        logger.info("Importing api.main...")
        from api.main import app
        logger.info("  ✓ api.main imported successfully")

        # Get port
        port = int(os.environ.get("PORT", 8000))
        logger.info(f"Starting uvicorn on port {port}...")

        # Start server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )

    except ImportError as e:
        logger.error("=" * 60)
        logger.error("IMPORT ERROR!")
        logger.error("=" * 60)
        logger.error(f"Failed to import: {e}")
        logger.error(f"Module: {e.name if hasattr(e, 'name') else 'unknown'}")
        logger.error(f"Path: {e.path if hasattr(e, 'path') else 'unknown'}")
        logger.error("\nTraceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 60)
        sys.exit(1)

    except Exception as e:
        logger.error("=" * 60)
        logger.error("STARTUP FAILED!")
        logger.error("=" * 60)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("\nFull traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
