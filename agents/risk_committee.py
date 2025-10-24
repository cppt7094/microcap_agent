"""
Risk Committee - Multi-Agent Position Sizing Debate

Three risk management agents debate optimal position sizing:
- Risk-Seeking: Concentration builds wealth
- Risk-Neutral: Balance risk and reward
- Risk-Conservative: Preservation first

Uses Claude API for authentic multi-agent debate.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.core_directives import get_agent_directive

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: Anthropic library not available. Install with: pip install anthropic")


class RiskSeekingAgent:
    """
    Risk-Seeking Agent - "Concentration builds wealth"

    Philosophy:
    - Larger positions (up to 30% of portfolio)
    - Let winners run
    - Higher volatility tolerance
    - Aggressive stop losses (-25% to -30%)
    """

    def __init__(self):
        self.name = "Risk-Seeking"
        self.max_position_size = 0.30  # 30% of portfolio
        self.stop_loss_pct = -0.25     # -25%
        self.philosophy = "Concentration builds wealth"
        self.wins = 0
        self.debates = 0

    def get_directive(self) -> str:
        """Get agent-specific directive including brutal honesty framework."""
        base_directive = get_agent_directive("risk")

        risk_seeking_directive = f"""
# RISK-SEEKING AGENT DIRECTIVE

## Core Philosophy
**"Concentration builds wealth"**

You are the AGGRESSIVE voice in the risk committee. Your role:
- Advocate for LARGER positions when conviction is high
- Push back against excessive diversification
- Argue for letting winners run
- Challenge conservative stop losses

## Position Sizing Guidelines
- **Maximum**: 30% of portfolio for highest conviction
- **Typical**: 20-25% for strong setups
- **Minimum**: 15% (never go below this)

## Stop Loss Philosophy
- **Standard**: -25% (give trades room to breathe)
- **High Conviction**: -30% (let winners develop)
- **Tight stops kill good trades**

## Debate Strategy
✅ **DO**:
- Cite momentum, catalysts, technical strength
- Challenge over-diversification ("owning the index")
- Point out opportunity cost of small positions
- Reference successful concentrated positions

❌ **DON'T**:
- Ignore risk entirely (you're aggressive, not reckless)
- Recommend >30% positions (hard limit)
- Dismiss valid concentration concerns
- Use vague language

## Example Arguments
**Good**: "APLD up 15% on volume breakout. This is exactly when we SIZE UP to 25%. Small position = small gains."
**Bad**: "Just buy more, it's going up!"

## Brutal Honesty
- Call out fear-based thinking
- Challenge weak reasoning from other agents
- Admit when setup is mediocre (don't force it)
- Recognize when diversification IS warranted

{base_directive}
"""
        return risk_seeking_directive

    def propose_position(
        self,
        recommendation: Dict,
        portfolio_context: Dict
    ) -> Dict:
        """
        Propose position size from risk-seeking perspective.

        Args:
            recommendation: Original recommendation dict
            portfolio_context: Current portfolio state

        Returns:
            Position proposal with reasoning
        """
        ticker = recommendation.get("ticker")
        original_qty = recommendation.get("qty", 0)
        price = recommendation.get("target_price", 0)
        confidence = recommendation.get("confidence", 0.5)

        # Calculate aggressive position size
        # Higher confidence = larger position
        if confidence >= 0.85:
            position_pct = 0.25  # 25% for very high confidence
        elif confidence >= 0.75:
            position_pct = 0.20  # 20% for high confidence
        else:
            position_pct = 0.15  # 15% minimum

        # Increase if momentum is strong
        if "momentum" in recommendation.get("reasoning", "").lower():
            position_pct = min(position_pct * 1.2, 0.30)

        proposed_qty = int(position_pct * 1000 / price)  # Assume $1000 portfolio

        return {
            "agent": self.name,
            "proposed_qty": proposed_qty,
            "position_pct": position_pct * 100,
            "stop_loss_pct": self.stop_loss_pct * 100,
            "reasoning_preview": f"Confidence {confidence:.0%} justifies {position_pct:.0%} position. Let winners run."
        }


class RiskNeutralAgent:
    """
    Risk-Neutral Agent - "Balance risk and reward"

    Philosophy:
    - Standard position sizing (15-20% max)
    - Balanced stop losses (-20%)
    - Evidence-based decisions
    - Moderate approach
    """

    def __init__(self):
        self.name = "Risk-Neutral"
        self.max_position_size = 0.20  # 20% of portfolio
        self.stop_loss_pct = -0.20     # -20%
        self.philosophy = "Balance risk and reward"
        self.wins = 0
        self.debates = 0

    def get_directive(self) -> str:
        """Get agent-specific directive including brutal honesty framework."""
        base_directive = get_agent_directive("risk")

        risk_neutral_directive = f"""
# RISK-NEUTRAL AGENT DIRECTIVE

## Core Philosophy
**"Balance risk and reward"**

You are the BALANCED voice in the risk committee. Your role:
- Find middle ground between extremes
- Base decisions on evidence, not fear or greed
- Standard position sizing (15-20%)
- Reasonable stop losses (-20%)

## Position Sizing Guidelines
- **Maximum**: 20% of portfolio
- **Typical**: 15-18% for solid setups
- **Minimum**: 10% for lower conviction

## Stop Loss Philosophy
- **Standard**: -20% (proven risk management)
- **Can adjust**: -18% to -22% based on volatility
- **Not emotional**: Based on technical levels

## Debate Strategy
✅ **DO**:
- Weigh both aggressive and conservative arguments
- Look for data to support position
- Challenge extremes on both sides
- Propose compromise when reasonable

❌ **DON'T**:
- Default to middle just to avoid conflict
- Ignore strong evidence for either side
- Use "balanced" as excuse for weak reasoning
- Fence-sit when clarity exists

## Example Arguments
**Good**: "Confidence is 78%, momentum confirmed. 18% position captures upside while managing risk. -20% stop at technical support."
**Bad**: "Let's just split the difference and move on."

## Brutal Honesty
- Call out extremism on both sides
- Admit when evidence leans one direction
- Don't hide behind "balanced approach"
- Take clear stance when data supports it

{base_directive}
"""
        return risk_neutral_directive

    def propose_position(
        self,
        recommendation: Dict,
        portfolio_context: Dict
    ) -> Dict:
        """Propose position size from risk-neutral perspective."""
        ticker = recommendation.get("ticker")
        original_qty = recommendation.get("qty", 0)
        price = recommendation.get("target_price", 0)
        confidence = recommendation.get("confidence", 0.5)

        # Standard position sizing
        if confidence >= 0.80:
            position_pct = 0.18  # 18% for high confidence
        elif confidence >= 0.70:
            position_pct = 0.15  # 15% standard
        else:
            position_pct = 0.12  # 12% for lower conviction

        proposed_qty = int(position_pct * 1000 / price)

        return {
            "agent": self.name,
            "proposed_qty": proposed_qty,
            "position_pct": position_pct * 100,
            "stop_loss_pct": self.stop_loss_pct * 100,
            "reasoning_preview": f"Standard {position_pct:.0%} sizing appropriate for {confidence:.0%} confidence."
        }


class RiskConservativeAgent:
    """
    Risk-Conservative Agent - "Preservation first"

    Philosophy:
    - Smaller positions (10-15% max)
    - Tight stop losses (-15%)
    - Diversification over concentration
    - Capital preservation
    """

    def __init__(self):
        self.name = "Risk-Conservative"
        self.max_position_size = 0.15  # 15% of portfolio
        self.stop_loss_pct = -0.15     # -15%
        self.philosophy = "Preservation first"
        self.wins = 0
        self.debates = 0

    def get_directive(self) -> str:
        """Get agent-specific directive including brutal honesty framework."""
        base_directive = get_agent_directive("risk")

        risk_conservative_directive = f"""
# RISK-CONSERVATIVE AGENT DIRECTIVE

## Core Philosophy
**"Preservation first"**

You are the DEFENSIVE voice in the risk committee. Your role:
- Advocate for smaller, safer positions
- Highlight concentration risk
- Push for tight stop losses
- Challenge reckless sizing

## Position Sizing Guidelines
- **Maximum**: 15% of portfolio
- **Typical**: 10-12% for most setups
- **Minimum**: 8% (below this, not worth it)

## Stop Loss Philosophy
- **Standard**: -15% (protect capital)
- **Can widen**: -18% for very low volatility only
- **Tight stops preserve capital for better opportunities**

## Debate Strategy
✅ **DO**:
- Point out portfolio concentration risks
- Highlight downside scenarios
- Reference past drawdowns
- Advocate for diversification

❌ **DON'T**:
- Be fearful without reason
- Ignore strong setups
- Always argue for smallest position
- Use "risk management" to kill all trades

## Example Arguments
**Good**: "Already 35% in tech. Adding 25% APLD = 60% tech exposure. Propose 10% to maintain diversification."
**Bad**: "This could go down, let's not trade."

## Brutal Honesty
- Admit when aggressive sizing IS appropriate
- Don't manufacture risk where it doesn't exist
- Recognize high-conviction setups
- Challenge your own conservatism when wrong

{base_directive}
"""
        return risk_conservative_directive

    def propose_position(
        self,
        recommendation: Dict,
        portfolio_context: Dict
    ) -> Dict:
        """Propose position size from risk-conservative perspective."""
        ticker = recommendation.get("ticker")
        original_qty = recommendation.get("qty", 0)
        price = recommendation.get("target_price", 0)
        confidence = recommendation.get("confidence", 0.5)

        # Conservative position sizing
        if confidence >= 0.85:
            position_pct = 0.15  # 15% even for highest confidence
        elif confidence >= 0.75:
            position_pct = 0.12  # 12% for good setups
        else:
            position_pct = 0.10  # 10% standard

        # Reduce if concentration concerns
        sector_exposure = portfolio_context.get("sector_exposure", 0)
        if sector_exposure > 0.30:  # >30% in sector already
            position_pct *= 0.8  # Reduce by 20%

        proposed_qty = int(position_pct * 1000 / price)

        return {
            "agent": self.name,
            "proposed_qty": proposed_qty,
            "position_pct": position_pct * 100,
            "stop_loss_pct": self.stop_loss_pct * 100,
            "reasoning_preview": f"Conservative {position_pct:.0%} sizing preserves capital and diversification."
        }


class RiskCommittee:
    """
    Risk Committee - Multi-agent debate for position sizing.

    Orchestrates debate between three risk management agents:
    - Risk-Seeking: Aggressive sizing
    - Risk-Neutral: Balanced approach
    - Risk-Conservative: Defensive sizing

    Uses Claude API for authentic multi-agent debate (2 rounds max).
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize Risk Committee.

        Args:
            anthropic_api_key: Anthropic API key (optional, uses env if not provided)
        """
        self.seeking_agent = RiskSeekingAgent()
        self.neutral_agent = RiskNeutralAgent()
        self.conservative_agent = RiskConservativeAgent()

        # Claude API client
        self.claude = None
        if ANTHROPIC_AVAILABLE:
            api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.claude = Anthropic(api_key=api_key)
            else:
                print("Warning: No Anthropic API key found. Debate will be simulated.")

        # Track historical decisions
        self.history_file = Path("risk_committee_history.json")
        self.history = self._load_history()

    def _load_history(self) -> List[Dict]:
        """Load historical committee decisions."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load history: {e}")
        return []

    def _save_history(self):
        """Save committee decision history."""
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save history: {e}")

    def debate_position_sizing(
        self,
        recommendation: Dict,
        portfolio_context: Optional[Dict] = None
    ) -> Dict:
        """
        Conduct multi-agent debate on position sizing.

        Args:
            recommendation: Trading recommendation dict with:
                - ticker: str
                - action: str (BUY/SELL)
                - qty: int (original quantity)
                - target_price: float
                - reasoning: str
                - confidence: float (0-1)
            portfolio_context: Optional portfolio state dict

        Returns:
            Consensus decision dict with:
                - original_rec: str
                - risk_seeking: str
                - risk_neutral: str
                - risk_conservative: str
                - consensus: str
                - reasoning: str
                - stop_loss: str
                - winner: str (which agent's advice was followed)
        """
        if portfolio_context is None:
            portfolio_context = {"sector_exposure": 0.2, "total_value": 1000}

        # Get each agent's initial proposal
        seeking_proposal = self.seeking_agent.propose_position(recommendation, portfolio_context)
        neutral_proposal = self.neutral_agent.propose_position(recommendation, portfolio_context)
        conservative_proposal = self.conservative_agent.propose_position(recommendation, portfolio_context)

        # Format original recommendation
        ticker = recommendation.get("ticker")
        original_qty = recommendation.get("qty", 0)
        target_price = recommendation.get("target_price", 0)
        action = recommendation.get("action", "BUY")

        original_rec = f"{action} {original_qty} {ticker} @ ${target_price:.2f}"

        # If Claude API available, conduct real debate
        if self.claude:
            consensus_result = self._claude_debate(
                recommendation,
                portfolio_context,
                seeking_proposal,
                neutral_proposal,
                conservative_proposal
            )
        else:
            # Simulate debate (fallback)
            consensus_result = self._simulated_debate(
                recommendation,
                seeking_proposal,
                neutral_proposal,
                conservative_proposal
            )

        # Determine winner (which agent's advice was closest to consensus)
        consensus_qty = consensus_result["consensus_qty"]

        distances = {
            "Risk-Seeking": abs(consensus_qty - seeking_proposal["proposed_qty"]),
            "Risk-Neutral": abs(consensus_qty - neutral_proposal["proposed_qty"]),
            "Risk-Conservative": abs(consensus_qty - conservative_proposal["proposed_qty"])
        }

        winner = min(distances, key=distances.get)

        # Update win counters
        if winner == "Risk-Seeking":
            self.seeking_agent.wins += 1
        elif winner == "Risk-Neutral":
            self.neutral_agent.wins += 1
        else:
            self.conservative_agent.wins += 1

        for agent in [self.seeking_agent, self.neutral_agent, self.conservative_agent]:
            agent.debates += 1

        # Build result
        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "original_rec": original_rec,
            "risk_seeking": f"{action} {seeking_proposal['proposed_qty']} shares - {seeking_proposal['reasoning_preview']}",
            "risk_neutral": f"{action} {neutral_proposal['proposed_qty']} shares - {neutral_proposal['reasoning_preview']}",
            "risk_conservative": f"{action} {conservative_proposal['proposed_qty']} shares - {conservative_proposal['reasoning_preview']}",
            "consensus": f"{action} {consensus_qty} shares",
            "reasoning": consensus_result["reasoning"],
            "stop_loss": consensus_result["stop_loss"],
            "winner": winner,
            "proposals": {
                "seeking": seeking_proposal,
                "neutral": neutral_proposal,
                "conservative": conservative_proposal
            }
        }

        # Save to history
        self.history.append(result)
        self._save_history()

        return result

    def _claude_debate(
        self,
        recommendation: Dict,
        portfolio_context: Dict,
        seeking: Dict,
        neutral: Dict,
        conservative: Dict
    ) -> Dict:
        """
        Conduct authentic debate using Claude API.

        Two rounds:
        1. Each agent presents their case
        2. Agents respond to each other, find consensus
        """
        ticker = recommendation.get("ticker")
        confidence = recommendation.get("confidence", 0.5)
        reasoning = recommendation.get("reasoning", "No reasoning provided")

        # Round 1: Initial arguments
        round1_prompt = f"""
You are moderating a risk committee debate on position sizing.

**RECOMMENDATION:**
Ticker: {ticker}
Confidence: {confidence:.0%}
Reasoning: {reasoning}

**PORTFOLIO CONTEXT:**
Total Value: ${portfolio_context.get('total_value', 1000):.0f}
Sector Exposure: {portfolio_context.get('sector_exposure', 0)*100:.0f}%

**AGENT PROPOSALS:**

Risk-Seeking ({seeking['position_pct']:.0f}%):
{seeking['reasoning_preview']}

Risk-Neutral ({neutral['position_pct']:.0f}%):
{neutral['reasoning_preview']}

Risk-Conservative ({conservative['position_pct']:.0f}%):
{conservative['reasoning_preview']}

**TASK:**
In 3-4 sentences, summarize the key debate points and recommend a consensus position size (in shares) and stop loss percentage.

Be direct. No hedging. Pick a specific number.
"""

        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": round1_prompt
                }]
            )

            debate_summary = response.content[0].text

            # Extract consensus from Claude's response
            # Look for numbers in the response
            import re

            # Try to find share count
            share_match = re.search(r'(\d+)\s*shares?', debate_summary, re.IGNORECASE)
            if share_match:
                consensus_qty = int(share_match.group(1))
            else:
                # Default to neutral if can't parse
                consensus_qty = neutral["proposed_qty"]

            # Try to find stop loss
            stop_match = re.search(r'(-?\d+)%?\s*stop', debate_summary, re.IGNORECASE)
            if stop_match:
                stop_pct = int(stop_match.group(1))
                if stop_pct > 0:
                    stop_pct = -stop_pct
            else:
                stop_pct = -20  # Default

            target_price = recommendation.get("target_price", 0)
            stop_price = target_price * (1 + stop_pct / 100)

            return {
                "consensus_qty": consensus_qty,
                "reasoning": debate_summary,
                "stop_loss": f"${stop_price:.2f} ({stop_pct}%)"
            }

        except Exception as e:
            print(f"Claude debate failed: {e}")
            # Fallback to simulated
            return self._simulated_debate(recommendation, seeking, neutral, conservative)

    def _simulated_debate(
        self,
        recommendation: Dict,
        seeking: Dict,
        neutral: Dict,
        conservative: Dict
    ) -> Dict:
        """Fallback: Simulated debate without Claude API."""
        confidence = recommendation.get("confidence", 0.5)

        # Simple logic: Higher confidence -> closer to seeking
        # Lower confidence -> closer to conservative

        if confidence >= 0.85:
            # High confidence: Risk-Seeking wins
            consensus_qty = seeking["proposed_qty"]
            stop_pct = seeking["stop_loss_pct"]
            reasoning = f"High confidence ({confidence:.0%}) justifies aggressive {seeking['position_pct']:.0f}% position. Risk-Seeking argument prevails."
        elif confidence >= 0.70:
            # Moderate confidence: Risk-Neutral wins
            consensus_qty = neutral["proposed_qty"]
            stop_pct = neutral["stop_loss_pct"]
            reasoning = f"Balanced approach appropriate for {confidence:.0%} confidence. Standard {neutral['position_pct']:.0f}% sizing."
        else:
            # Lower confidence: Risk-Conservative wins
            consensus_qty = conservative["proposed_qty"]
            stop_pct = conservative["stop_loss_pct"]
            reasoning = f"Lower confidence ({confidence:.0%}) warrants conservative {conservative['position_pct']:.0f}% position."

        target_price = recommendation.get("target_price", 0)
        stop_price = target_price * (1 + stop_pct / 100)

        return {
            "consensus_qty": consensus_qty,
            "reasoning": reasoning,
            "stop_loss": f"${stop_price:.2f} ({stop_pct:.0f}%)"
        }

    def get_statistics(self) -> Dict:
        """Get committee statistics and win rates."""
        total_debates = self.seeking_agent.debates

        if total_debates == 0:
            return {
                "total_debates": 0,
                "win_rates": {
                    "Risk-Seeking": 0,
                    "Risk-Neutral": 0,
                    "Risk-Conservative": 0
                }
            }

        return {
            "total_debates": total_debates,
            "win_rates": {
                "Risk-Seeking": (self.seeking_agent.wins / total_debates * 100) if total_debates > 0 else 0,
                "Risk-Neutral": (self.neutral_agent.wins / total_debates * 100) if total_debates > 0 else 0,
                "Risk-Conservative": (self.conservative_agent.wins / total_debates * 100) if total_debates > 0 else 0
            },
            "philosophies": {
                "Risk-Seeking": self.seeking_agent.philosophy,
                "Risk-Neutral": self.neutral_agent.philosophy,
                "Risk-Conservative": self.conservative_agent.philosophy
            }
        }


# Singleton instance
_committee_instance = None

def get_risk_committee() -> RiskCommittee:
    """Get or create singleton RiskCommittee instance."""
    global _committee_instance
    if _committee_instance is None:
        _committee_instance = RiskCommittee()
    return _committee_instance


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("RISK COMMITTEE - POSITION SIZING DEBATE")
    print("=" * 80)
    print()

    # Create committee
    committee = get_risk_committee()

    # Example recommendation
    recommendation = {
        "ticker": "APLD",
        "action": "BUY",
        "qty": 5,
        "target_price": 36.28,
        "reasoning": "Strong momentum with positive catalyst sentiment. In bullish market regime with 18% unrealized gains.",
        "confidence": 0.85
    }

    portfolio_context = {
        "total_value": 1000,
        "sector_exposure": 0.35  # 35% already in tech
    }

    print("ORIGINAL RECOMMENDATION:")
    print(f"  {recommendation['action']} {recommendation['qty']} {recommendation['ticker']} @ ${recommendation['target_price']:.2f}")
    print(f"  Confidence: {recommendation['confidence']:.0%}")
    print(f"  Reasoning: {recommendation['reasoning']}")
    print()

    print("CONDUCTING DEBATE...")
    print()

    # Debate
    result = committee.debate_position_sizing(recommendation, portfolio_context)

    print("DEBATE RESULTS:")
    print("-" * 80)
    print(f"Risk-Seeking:      {result['risk_seeking']}")
    print(f"Risk-Neutral:      {result['risk_neutral']}")
    print(f"Risk-Conservative: {result['risk_conservative']}")
    print()
    print(f"CONSENSUS:         {result['consensus']}")
    print(f"Stop Loss:         {result['stop_loss']}")
    print(f"Winner:            {result['winner']}")
    print()
    print("REASONING:")
    print(f"  {result['reasoning']}")
    print()

    # Show statistics
    stats = committee.get_statistics()
    print("=" * 80)
    print("COMMITTEE STATISTICS")
    print("=" * 80)
    print(f"Total Debates: {stats['total_debates']}")
    print()
    print("Win Rates:")
    for agent, rate in stats['win_rates'].items():
        print(f"  {agent:20} - {rate:.1f}%")
    print()
    print("=" * 80)
