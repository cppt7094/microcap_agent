"""
Intelligent Cache Manager with Market-Aware TTL
Wraps simple_cache.py with smart caching based on market hours
"""
import sys
import os
from datetime import datetime, time
from typing import Any, Callable, Optional
import pytz
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simple_cache import SimpleCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheManager:
    """
    Intelligent cache manager with market-aware TTL settings

    Cache TTL Strategy:
    - Market hours (9:30 AM - 4 PM ET Mon-Fri): 60 seconds
    - After hours (4 PM - 9:30 AM ET weekdays): 5 minutes (300 seconds)
    - Weekends: 1 hour (3600 seconds)
    """

    # Market hours configuration (Eastern Time)
    MARKET_OPEN_TIME = time(9, 30)   # 9:30 AM ET
    MARKET_CLOSE_TIME = time(16, 0)  # 4:00 PM ET

    # Cache TTL in seconds
    TTL_MARKET_HOURS = 60        # 1 minute during market hours
    TTL_AFTER_HOURS = 300        # 5 minutes after hours
    TTL_WEEKEND = 3600           # 1 hour on weekends

    def __init__(self, cache_dir: str = 'cache'):
        """Initialize cache manager with underlying SimpleCache"""
        self.cache = SimpleCache(cache_dir=cache_dir)
        self.stats = {
            'hits': 0,
            'misses': 0,
            'fetches': 0
        }
        logger.info("🗄️  CacheManager initialized")

    def is_market_open(self) -> bool:
        """
        Check if US stock market is currently open

        Returns:
            bool: True if market is open, False otherwise
        """
        # Get current time in Eastern Time
        et_tz = pytz.timezone('US/Eastern')
        now_et = datetime.now(et_tz)

        # Check if weekend (Saturday=5, Sunday=6)
        if now_et.weekday() >= 5:
            return False

        # Check if within market hours
        current_time = now_et.time()
        is_open = self.MARKET_OPEN_TIME <= current_time <= self.MARKET_CLOSE_TIME

        return is_open

    def get_intelligent_ttl(self) -> int:
        """
        Get TTL in seconds based on current market conditions

        Returns:
            int: TTL in seconds
        """
        et_tz = pytz.timezone('US/Eastern')
        now_et = datetime.now(et_tz)

        # Weekend caching
        if now_et.weekday() >= 5:
            logger.debug(f"📅 Weekend detected - using {self.TTL_WEEKEND}s TTL")
            return self.TTL_WEEKEND

        # Market hours caching
        if self.is_market_open():
            logger.debug(f"📈 Market open - using {self.TTL_MARKET_HOURS}s TTL")
            return self.TTL_MARKET_HOURS

        # After hours caching
        logger.debug(f"🌙 After hours - using {self.TTL_AFTER_HOURS}s TTL")
        return self.TTL_AFTER_HOURS

    async def get_or_fetch(
        self,
        key: str,
        fetch_function: Callable,
        ttl_seconds: Optional[int] = None
    ) -> Any:
        """
        Get cached data or fetch if not available/expired

        Args:
            key: Cache key
            fetch_function: Async or sync function to call if cache miss
            ttl_seconds: Optional override for TTL (uses intelligent TTL if None)

        Returns:
            Cached or freshly fetched data
        """
        # Use intelligent TTL if not specified
        if ttl_seconds is None:
            ttl_seconds = self.get_intelligent_ttl()

        # Convert seconds to minutes for SimpleCache
        ttl_minutes = ttl_seconds / 60

        # Try to get from cache
        cached_value = self.cache.get(key, max_age_minutes=ttl_minutes)

        if cached_value is not None:
            self.stats['hits'] += 1
            logger.info(f"✓ Cache HIT: {key} (TTL: {ttl_seconds}s)")
            return cached_value

        # Cache miss - fetch fresh data
        self.stats['misses'] += 1
        self.stats['fetches'] += 1
        logger.info(f"✗ Cache MISS: {key} - fetching fresh data")

        try:
            # Call fetch function (handle both sync and async)
            if hasattr(fetch_function, '__call__'):
                # Check if it's a coroutine
                import asyncio
                if asyncio.iscoroutinefunction(fetch_function):
                    value = await fetch_function()
                else:
                    value = fetch_function()
            else:
                value = fetch_function

            # Cache the result
            self.cache.set(key, value)
            logger.info(f"💾 Cached: {key} (TTL: {ttl_seconds}s)")

            return value

        except Exception as e:
            logger.error(f"❌ Error fetching data for {key}: {e}")
            raise

    def invalidate(self, key: str) -> bool:
        """
        Invalidate (delete) a specific cache entry

        Args:
            key: Cache key to invalidate

        Returns:
            bool: True if cache entry was deleted, False if not found
        """
        try:
            cache_file = self.cache.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"🗑️  Invalidated cache: {key}")
                return True
            else:
                logger.warning(f"⚠️  Cache key not found: {key}")
                return False
        except Exception as e:
            logger.error(f"❌ Error invalidating cache {key}: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern

        Args:
            pattern: Glob pattern (e.g., "portfolio_*")

        Returns:
            int: Number of entries invalidated
        """
        count = 0
        try:
            for cache_file in self.cache.cache_dir.glob(f"{pattern}.json"):
                cache_file.unlink()
                count += 1

            if count > 0:
                logger.info(f"🗑️  Invalidated {count} cache entries matching: {pattern}")

            return count
        except Exception as e:
            logger.error(f"❌ Error invalidating pattern {pattern}: {e}")
            return count

    def get_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            dict: Cache hit rate, total hits, misses, and fetches
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        market_status = "OPEN" if self.is_market_open() else "CLOSED"
        current_ttl = self.get_intelligent_ttl()

        return {
            'hit_rate_percent': round(hit_rate, 2),
            'total_hits': self.stats['hits'],
            'total_misses': self.stats['misses'],
            'total_fetches': self.stats['fetches'],
            'total_requests': total_requests,
            'market_status': market_status,
            'current_ttl_seconds': current_ttl,
            'market_open': self.is_market_open()
        }

    def clear_all(self):
        """Clear entire cache"""
        try:
            self.cache.clear()
            logger.info("🗑️  Cleared entire cache")
        except Exception as e:
            logger.error(f"❌ Error clearing cache: {e}")

    def clear_expired(self):
        """Remove expired cache entries"""
        try:
            ttl_minutes = self.get_intelligent_ttl() / 60
            self.cache.clear_expired(max_age_minutes=ttl_minutes)
            logger.info(f"🧹 Cleared expired cache entries (TTL: {ttl_minutes}m)")
        except Exception as e:
            logger.error(f"❌ Error clearing expired cache: {e}")

    def get(self, key: str, max_age_minutes: Optional[float] = None) -> Any:
        """
        Get value from cache (direct access)

        Args:
            key: Cache key
            max_age_minutes: Maximum age in minutes (uses intelligent TTL if None)

        Returns:
            Cached value or None if not found/expired
        """
        if max_age_minutes is None:
            max_age_minutes = self.get_intelligent_ttl() / 60

        return self.cache.get(key, max_age_minutes=max_age_minutes)

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in cache (direct access)

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (uses intelligent TTL if None)
        """
        # Note: SimpleCache doesn't use TTL on set, only on get
        # TTL is enforced when retrieving via max_age_minutes
        self.cache.set(key, value)

        ttl = ttl_seconds if ttl_seconds else self.get_intelligent_ttl()
        logger.info(f"💾 Cached: {key} (TTL: {ttl}s)")

    def get_cache_age(self, key: str) -> Optional[int]:
        """
        Get age of cached entry in seconds

        Args:
            key: Cache key

        Returns:
            Age in seconds or None if not found
        """
        try:
            cache_file = self.cache.cache_dir / f"{key}.json"
            if cache_file.exists():
                import time
                file_mtime = cache_file.stat().st_mtime
                age_seconds = int(time.time() - file_mtime)
                return age_seconds
            return None
        except Exception as e:
            logger.error(f"❌ Error getting cache age for {key}: {e}")
            return None


# Singleton instance for API-wide use
cache_manager = CacheManager()


# Convenience functions
def is_market_open() -> bool:
    """Check if market is currently open"""
    return cache_manager.is_market_open()


def get_cache_stats() -> dict:
    """Get current cache statistics"""
    return cache_manager.get_stats()


def invalidate_cache(key: str) -> bool:
    """Invalidate a specific cache entry"""
    return cache_manager.invalidate(key)


# Example usage
if __name__ == "__main__":
    import asyncio

    async def example():
        # Create cache manager
        cm = CacheManager()

        # Check market status
        print(f"\n{'='*60}")
        print("Market Status Check")
        print(f"{'='*60}")
        print(f"Market Open: {cm.is_market_open()}")
        print(f"Current TTL: {cm.get_intelligent_ttl()}s")

        # Test cache operations
        print(f"\n{'='*60}")
        print("Cache Operations Test")
        print(f"{'='*60}")

        # Define a fetch function
        def fetch_data():
            print("  Fetching fresh data...")
            return {"data": "test_value", "timestamp": datetime.now().isoformat()}

        # First call - cache miss
        result1 = await cm.get_or_fetch("test_key", fetch_data)
        print(f"First call result: {result1}")

        # Second call - cache hit
        result2 = await cm.get_or_fetch("test_key", fetch_data)
        print(f"Second call result: {result2}")

        # Get stats
        print(f"\n{'='*60}")
        print("Cache Statistics")
        print(f"{'='*60}")
        stats = cm.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        # Invalidate cache
        print(f"\n{'='*60}")
        print("Cache Invalidation")
        print(f"{'='*60}")
        cm.invalidate("test_key")

        # Third call - cache miss again
        result3 = await cm.get_or_fetch("test_key", fetch_data)
        print(f"Third call result: {result3}")

        # Final stats
        print(f"\n{'='*60}")
        print("Final Cache Statistics")
        print(f"{'='*60}")
        stats = cm.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

    # Run example
    asyncio.run(example())
