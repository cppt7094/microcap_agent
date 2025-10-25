"""
Data file path utilities for Railway compatibility.

Railway has a read-only filesystem except /tmp.
This helper ensures data files are written to the correct location.
"""
import os


def get_data_path(filename: str) -> str:
    """
    Get the correct path for data files.

    - On Railway: /tmp/{filename} (ephemeral, survives during deployment)
    - Locally: {filename} (current directory)

    Args:
        filename: The name of the data file (e.g., "api_usage.json")

    Returns:
        Full path to the data file
    """
    if os.getenv("RAILWAY_ENVIRONMENT"):
        # Running on Railway - use /tmp
        return f"/tmp/{filename}"
    else:
        # Running locally - use current directory
        return filename


def ensure_data_dir_exists():
    """
    Ensure the data directory exists (no-op on Railway since /tmp always exists).
    """
    if not os.getenv("RAILWAY_ENVIRONMENT"):
        # Locally, create data directories if needed
        os.makedirs("cache", exist_ok=True)
