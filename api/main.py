"""
Project Tehama API - FastAPI Application
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Optional
import os

from api.models import PortfolioSummary, Alert, Recommendation
from api.services import (
    portfolio_service,
    alert_service,
    recommendation_service,
    agent_service
)
from api.cache_manager import cache_manager
from api.usage_tracker import usage_tracker
from agents.opportunity_scanner import get_scanner

# Get singleton scanner instance
opportunity_scanner = get_scanner()

# Create FastAPI app instance
app = FastAPI(
    title="Project Tehama API",
    description="Real-time microcap trading intelligence API",
    version="1.0.0"
)

# Configure CORS - Allow localhost and file:// for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "null"  # Allow file:// protocol
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Dashboard not found. Please ensure frontend/index.html exists."}


@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Serve diagnostic test page"""
    test_path = os.path.join(FRONTEND_DIR, "test.html")
    if os.path.exists(test_path):
        return FileResponse(test_path)
    return {"message": "Test page not found."}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/portfolio", response_model=PortfolioSummary)
async def get_portfolio(nocache: bool = Query(default=False)):
    """
    Get current portfolio summary including all positions

    Args:
        nocache: Set to true to bypass cache and fetch fresh data

    Returns:
        PortfolioSummary with total value, cash, daily changes, and all positions
    """
    # Note: PortfolioService doesn't have use_cache parameter yet
    # Will return cached data by default through cache_manager
    return await portfolio_service.get_portfolio_summary()


@app.get("/api/alerts", response_model=List[Alert])
async def get_alerts(
    limit: int = Query(default=10, ge=1, le=100),
    nocache: bool = Query(default=False)
):
    """
    Get recent alerts and notifications

    Args:
        limit: Maximum number of alerts to return (1-100)
        nocache: Set to true to bypass cache and fetch fresh data

    Returns:
        List of recent alerts
    """
    return await alert_service.get_recent_alerts(limit=limit, use_cache=not nocache)


@app.get("/api/recommendations", response_model=List[Recommendation])
async def get_recommendations(
    status: Optional[str] = Query(default=None),
    nocache: bool = Query(default=False),
    apply_risk: bool = Query(default=False)
):
    """
    Get AI-generated trading recommendations

    Args:
        status: Filter by status (pending, accepted, rejected, executed)
        nocache: Set to true to bypass cache and fetch fresh data
        apply_risk: Apply Risk Committee position sizing debate

    Returns:
        List of recommendations
    """
    return await recommendation_service.get_recommendations(
        status=status,
        use_cache=not nocache,
        apply_risk=apply_risk
    )


@app.get("/api/recommendations/analyze/{ticker}")
async def analyze_ticker(
    ticker: str,
    apply_risk: bool = Query(default=False)
):
    """
    Generate live multi-agent recommendation for a specific ticker.

    Full pipeline:
    1. Run 4 analyst agents (Technical, Fundamental, Sentiment, Risk)
    2. Aggregate with Meta-Agent (applies diversity penalty for groupthink)
    3. Optionally apply Risk Committee for position sizing
    4. Return complete recommendation with agent breakdown

    Args:
        ticker: Stock ticker to analyze (e.g. APLD, NTLA)
        apply_risk: Apply Risk Committee position sizing debate

    Returns:
        Single recommendation with full agent analysis
    """
    # Get portfolio context for risk analysis
    try:
        portfolio = await portfolio_service.get_portfolio_summary()
        portfolio_context = {
            "total_value": portfolio.total_value,
            "cash": portfolio.cash,
            "positions": [
                {
                    "ticker": pos.ticker,
                    "market_value": pos.market_value,
                    "qty": pos.qty
                }
                for pos in portfolio.positions
            ]
        }
    except:
        portfolio_context = None

    # Generate multi-agent recommendation
    recommendation = recommendation_service._generate_multi_agent_recommendation(
        ticker=ticker.upper(),
        portfolio_context=portfolio_context
    )

    if not recommendation:
        return {
            "error": f"Failed to generate recommendation for {ticker}",
            "ticker": ticker
        }

    # Apply Risk Committee if requested
    if apply_risk and recommendation:
        risk_result = recommendation_service._apply_risk_committee(recommendation, portfolio_context)
        if risk_result:
            recommendation.reasoning += f"\n\n[Risk Committee] {risk_result['risk_debate_summary']}"
            recommendation.qty = risk_result['risk_adjusted_qty']

    return recommendation


@app.get("/api/agents/status")
async def get_agents_status(nocache: bool = Query(default=False)):
    """
    Get status of all AI agents

    Args:
        nocache: Set to true to bypass cache and fetch fresh data

    Returns:
        Status information for all active agents
    """
    return await agent_service.get_agent_status(use_cache=not nocache)


@app.get("/api/opportunities/scan")
async def scan_opportunities(
    limit: int = Query(default=10, ge=1, le=50),
    min_score: int = Query(default=60, ge=0, le=100)
):
    """
    Trigger a new opportunity scan across market universe.

    This is an expensive operation that scans 40+ tickers with real-time data.
    Results are cached for 2 hours to avoid excessive API calls.

    Args:
        limit: Maximum number of results to return (1-50, default 10)
        min_score: Minimum score threshold (0-100, default 60)

    Returns:
        List of opportunities with scores, signals, and reasoning
    """
    try:
        import time

        # Check cache first
        cache_key = f"opportunities_scan_{min_score}_{limit}"

        # Try to get from cache
        cached_data = cache_manager.get(cache_key)

        if cached_data:
            return {
                **cached_data,
                "cached": True,
                "cache_age_seconds": cache_manager.get_cache_age(cache_key)
            }

        # No cache, run new scan
        start_time = time.time()
        opportunities = opportunity_scanner.scan_for_opportunities(max_results=50)

        # Filter by min_score
        filtered = [opp for opp in opportunities if opp["score"] >= min_score]

        result = {
            "opportunities": filtered[:limit],
            "total_scanned": opportunity_scanner.last_scan_stats.get("tickers_scanned", 0),
            "total_found": len(filtered),
            "scan_time": opportunity_scanner.last_scan_stats.get("scan_time", "unknown"),
            "scanned_at": opportunity_scanner.last_scan_stats.get("timestamp"),
            "cached": False
        }

        # Cache for 2 hours (7200 seconds)
        cache_manager.set(cache_key, result, ttl_seconds=7200)

        return result

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Opportunity scan failed: {e}")
        return {
            "error": str(e),
            "opportunities": [],
            "total_scanned": 0,
            "total_found": 0,
            "cached": False
        }


@app.get("/api/opportunities/latest")
async def get_latest_opportunities(limit: int = Query(default=10, ge=1, le=50)):
    """
    Get cached results from last scan (fast, no new scan).

    Reads from opportunities_latest.json if available, otherwise triggers a scan.

    Args:
        limit: Maximum number of results to return (1-50, default 10)

    Returns:
        Cached opportunities from last scan
    """
    try:
        import json
        from pathlib import Path

        cache_file = Path("opportunities_latest.json")

        if cache_file.exists():
            with open(cache_file, "r") as f:
                data = json.load(f)
                opportunities = data.get("opportunities", [])

                return {
                    "opportunities": opportunities[:limit],
                    "scanned_at": data.get("scanned_at"),
                    "total_found": len(opportunities),
                    "stats": data.get("stats", {}),
                    "cached": True
                }
        else:
            # No cached data, trigger scan
            return await scan_opportunities(limit=limit, min_score=60)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to read cached opportunities: {e}")
        return {
            "error": str(e),
            "opportunities": [],
            "cached": False
        }


@app.get("/api/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics and performance metrics

    Returns:
        Cache hit rate, market status, TTL settings, and request counts
    """
    return cache_manager.get_stats()


@app.post("/api/cache/invalidate/{key}")
async def invalidate_cache(key: str):
    """
    Invalidate a specific cache entry

    Args:
        key: Cache key to invalidate

    Returns:
        Success status
    """
    success = cache_manager.invalidate(key)
    return {
        "success": success,
        "message": f"Cache key '{key}' {'invalidated' if success else 'not found'}"
    }


@app.post("/api/cache/clear")
async def clear_cache():
    """
    Clear entire cache (use with caution)

    Returns:
        Success status
    """
    cache_manager.clear_all()
    return {
        "success": True,
        "message": "Entire cache cleared"
    }


@app.get("/api/usage")
async def get_api_usage():
    """
    Get API usage statistics and monitoring data

    Returns:
        Comprehensive usage data including:
        - API call counts and limits per provider
        - Usage percentages and health status
        - Cache performance metrics
        - Next reset time
    """
    # Get raw usage stats from tracker
    usage_stats = usage_tracker.get_stats()

    # Get cache stats
    cache_stats = cache_manager.get_stats()

    # Build response with enhanced data
    response = {
        "date": usage_stats["date"],
        "apis": {},
        "cache": {
            "hit_rate": cache_stats.get("hit_rate", 0),
            "total_requests": cache_stats.get("total_requests", 0),
            "hits": cache_stats.get("hits", 0),
            "misses": cache_stats.get("misses", 0)
        },
        "last_updated": usage_stats.get("last_updated"),
        "next_reset": usage_stats.get("reset_at")
    }

    # Process each API's stats
    for api_name, api_data in usage_stats["apis"].items():
        calls = api_data["calls"]
        limit = api_data["limit"]

        response["apis"][api_name] = {
            "calls": calls,
            "limit": limit,
            "percent": round((calls / limit * 100), 1) if limit else 0,
            "status": api_data["status"]
        }

    return response


# Mount static files at the end (must be after all route definitions)
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
