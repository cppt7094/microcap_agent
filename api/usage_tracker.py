"""
API Usage Tracker
Monitors and tracks API usage across all data providers with daily limits
"""

import json
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Dict, Optional, Literal
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

StatusType = Literal["healthy", "warning", "critical"]


class UsageTracker:
    """
    Tracks API usage across all providers with automatic persistence and daily resets
    """

    # API daily limits
    API_LIMITS = {
        "alpaca": 12000,
        "alpha_vantage": 25,
        "fmp": 250,
        "newsapi": 100,
        "yfinance": None,  # Unlimited
        "cache": None  # Unlimited
    }

    def __init__(self, data_file: str = "api_usage.json"):
        """Initialize usage tracker with persistent storage"""
        self.data_file = Path(data_file)
        self.data = self._load_data()
        logger.info("UsageTracker initialized")

    def _get_current_date_et(self) -> str:
        """Get current date in ET timezone"""
        et_tz = pytz.timezone('US/Eastern')
        now_et = datetime.now(et_tz)
        return now_et.strftime('%Y-%m-%d')

    def _get_next_reset_time(self) -> str:
        """Calculate next midnight ET for reset"""
        et_tz = pytz.timezone('US/Eastern')
        now_et = datetime.now(et_tz)

        # Next midnight ET
        next_midnight = now_et.replace(hour=0, minute=0, second=0, microsecond=0)
        if now_et.hour >= 0:  # After midnight, go to next day
            from datetime import timedelta
            next_midnight = next_midnight + timedelta(days=1)

        return next_midnight.isoformat()

    def _load_data(self) -> Dict:
        """Load usage data from file or create new structure"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded usage data from {self.data_file}")

                    # Check if we need to reset (new day)
                    current_date = self._get_current_date_et()
                    if data.get('date') != current_date:
                        logger.info(f"New day detected, resetting usage data")
                        return self._create_new_data()

                    return data
            else:
                logger.info("No existing usage data found, creating new")
                return self._create_new_data()
        except Exception as e:
            logger.error(f"Error loading usage data: {e}")
            return self._create_new_data()

    def _create_new_data(self) -> Dict:
        """Create fresh usage data structure"""
        current_date = self._get_current_date_et()
        return {
            "date": current_date,
            "apis": {
                api_name: {
                    "calls": 0,
                    "limit": limit,
                    "status": "healthy",
                    "last_call": None
                }
                for api_name, limit in self.API_LIMITS.items()
            },
            "reset_at": self._get_next_reset_time()
        }

    def _save_data(self):
        """Persist usage data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            logger.debug(f"Saved usage data to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving usage data: {e}")

    def _check_and_reset(self):
        """Check if we need to reset for new day"""
        current_date = self._get_current_date_et()
        if self.data.get('date') != current_date:
            logger.info(f"Resetting usage data for new day: {current_date}")
            self.reset_daily()

    def get_status(self, api_name: str) -> StatusType:
        """
        Calculate status for an API based on usage percentage

        Returns:
            "healthy" if < 50% of limit
            "warning" if 50-80% of limit
            "critical" if > 80% of limit
            "healthy" for unlimited APIs
        """
        if api_name not in self.data['apis']:
            return "healthy"

        api_data = self.data['apis'][api_name]
        limit = api_data['limit']

        # Unlimited APIs are always healthy
        if limit is None:
            return "healthy"

        calls = api_data['calls']
        percent = (calls / limit) * 100

        if percent >= 80:
            return "critical"
        elif percent >= 50:
            return "warning"
        else:
            return "healthy"

    def increment(self, api_name: str):
        """
        Increment usage counter for an API

        Args:
            api_name: Name of the API to increment
        """
        # Check for daily reset
        self._check_and_reset()

        if api_name not in self.data['apis']:
            logger.warning(f"Unknown API name: {api_name}")
            return

        # Increment call count
        self.data['apis'][api_name]['calls'] += 1

        # Update last call time
        self.data['apis'][api_name]['last_call'] = datetime.now().isoformat()

        # Update status
        self.data['apis'][api_name]['status'] = self.get_status(api_name)

        # Log warning if approaching limit
        api_data = self.data['apis'][api_name]
        if api_data['limit'] is not None:
            percent = (api_data['calls'] / api_data['limit']) * 100
            if percent >= 80:
                logger.warning(
                    f"API {api_name} at {percent:.1f}% capacity "
                    f"({api_data['calls']}/{api_data['limit']})"
                )
            else:
                logger.info(
                    f"API {api_name} called: {api_data['calls']}/{api_data['limit']} "
                    f"({percent:.1f}%)"
                )
        else:
            logger.info(f"API {api_name} called: {api_data['calls']} (unlimited)")

        # Auto-save after every increment
        self._save_data()

    def get_stats(self) -> Dict:
        """
        Get current usage statistics

        Returns:
            Dictionary with all usage data including percentages
        """
        # Check for daily reset
        self._check_and_reset()

        stats = {
            "date": self.data['date'],
            "apis": {},
            "last_updated": datetime.now().isoformat(),
            "next_reset": self.data['reset_at']
        }

        for api_name, api_data in self.data['apis'].items():
            limit = api_data['limit']
            calls = api_data['calls']

            stats['apis'][api_name] = {
                "calls": calls,
                "limit": limit,
                "percent": (calls / limit * 100) if limit else 0,
                "status": self.get_status(api_name),
                "last_call": api_data.get('last_call')
            }

        return stats

    def reset_daily(self):
        """Reset all usage counters for a new day"""
        logger.info("Resetting daily usage counters")
        self.data = self._create_new_data()
        self._save_data()

    def get_warnings(self) -> list:
        """
        Get list of APIs that are in warning or critical status

        Returns:
            List of dictionaries with API name, status, and usage info
        """
        warnings = []
        for api_name, api_data in self.data['apis'].items():
            status = self.get_status(api_name)
            if status in ["warning", "critical"]:
                limit = api_data['limit']
                calls = api_data['calls']
                percent = (calls / limit * 100) if limit else 0

                warnings.append({
                    "api": api_name,
                    "status": status,
                    "calls": calls,
                    "limit": limit,
                    "percent": percent
                })

        return warnings


# Singleton instance
usage_tracker = UsageTracker()


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("API Usage Tracker Test")
    print("="*60)

    # Create tracker
    tracker = UsageTracker("test_api_usage.json")

    # Simulate some API calls
    print("\nSimulating API calls...")
    tracker.increment("alpaca")
    tracker.increment("alpaca")
    tracker.increment("yfinance")
    tracker.increment("alpha_vantage")
    tracker.increment("fmp")

    # Get stats
    print("\n" + "="*60)
    print("Current Usage Statistics:")
    print("="*60)
    stats = tracker.get_stats()

    for api_name, data in stats['apis'].items():
        if data['limit']:
            print(f"{api_name:15} - {data['calls']:4} / {data['limit']:5} ({data['percent']:.1f}%) - {data['status']}")
        else:
            print(f"{api_name:15} - {data['calls']:4} / Unlimited - {data['status']}")

    # Check for warnings
    print("\n" + "="*60)
    print("Warnings:")
    print("="*60)
    warnings = tracker.get_warnings()
    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning['api']} at {warning['percent']:.1f}% ({warning['calls']}/{warning['limit']})")
    else:
        print("No warnings - all APIs healthy")

    # Clean up test file
    import os
    if os.path.exists("test_api_usage.json"):
        os.remove("test_api_usage.json")
        print("\nTest file cleaned up")
