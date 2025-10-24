"""
Tehama Trading Agents Package

Multi-agent AI system for microcap trading intelligence.

This package implements trading agents that follow the Brutal Honesty Framework,
designed to provide direct, actionable analysis rather than sycophantic validation.

Core Philosophy:
- Truth > Validation
- Conviction > Hedging
- Actionability > Verbosity
- Harsh scoring makes high scores meaningful
"""

from .opportunity_scanner import OpportunityScannerAgent
from .core_directives import (
    get_agent_directive,
    get_scoring_guidelines,
    validate_recommendation_quality
)

__all__ = [
    'OpportunityScannerAgent',
    'get_agent_directive',
    'get_scoring_guidelines',
    'validate_recommendation_quality'
]
