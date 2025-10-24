"""
Pydantic Models for Project Tehama API
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Position(BaseModel):
    """Individual portfolio position"""
    ticker: str = Field(..., description="Stock ticker symbol")
    qty: float = Field(..., description="Quantity of shares held")
    avg_entry_price: float = Field(..., description="Average entry price per share")
    current_price: float = Field(..., description="Current market price per share")
    market_value: float = Field(..., description="Current market value of position")
    unrealized_plpc: float = Field(..., description="Unrealized P/L percent")
    daily_change_pct: float = Field(..., description="Today's percent change")


class PortfolioSummary(BaseModel):
    """Portfolio summary with all positions"""
    total_value: float = Field(..., description="Total portfolio value")
    cash: float = Field(..., description="Available cash balance")
    daily_change: float = Field(..., description="Today's dollar change")
    daily_change_pct: float = Field(..., description="Today's percent change")
    positions: List[Position] = Field(default_factory=list, description="List of all positions")


class Alert(BaseModel):
    """Trading alert or notification"""
    type: str = Field(..., description="Alert type (price_alert, news_alert, technical_alert, etc.)")
    ticker: Optional[str] = Field(None, description="Related ticker symbol")
    message: str = Field(..., description="Alert message")
    severity: str = Field(..., description="Severity level (info, warning, critical)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Alert timestamp")


class Recommendation(BaseModel):
    """AI-generated trading recommendation"""
    id: str = Field(..., description="Unique recommendation ID")
    ticker: str = Field(..., description="Stock ticker symbol")
    action: str = Field(..., description="Recommended action (BUY, SELL, HOLD, ADD, TRIM)")
    qty: Optional[float] = Field(None, description="Recommended quantity")
    target_price: Optional[float] = Field(None, description="Target price level")
    reasoning: str = Field(..., description="AI reasoning for recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    agents: List[str] = Field(default_factory=list, description="Contributing AI agents")
    status: str = Field(default="pending", description="Recommendation status (pending, accepted, rejected, executed)")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
