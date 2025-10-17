"""
Simple file-based cache to avoid API rate limits
"""
import json
from pathlib import Path
from datetime import datetime, timedelta


class SimpleCache:
    """Simple file-based cache to avoid API rate limits"""

    def __init__(self, cache_dir='cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get(self, key: str, max_age_minutes: int = 60):
        """Get cached data if not expired"""
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            # Check if expired
            cached_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cached_time > timedelta(minutes=max_age_minutes):
                return None

            return data['value']
        except Exception as e:
            # If cache is corrupted, return None
            print(f"Cache read error for {key}: {e}")
            return None

    def set(self, key: str, value: any):
        """Cache data with timestamp"""
        cache_file = self.cache_dir / f"{key}.json"

        data = {
            'timestamp': datetime.now().isoformat(),
            'value': value
        }

        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Cache write error for {key}: {e}")

    def clear(self):
        """Clear all cached data"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

    def clear_expired(self, max_age_minutes: int = 60):
        """Remove expired cache files"""
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)

                cached_time = datetime.fromisoformat(data['timestamp'])
                if cached_time < cutoff_time:
                    cache_file.unlink()
            except:
                # If we can't read it, delete it
                cache_file.unlink()
