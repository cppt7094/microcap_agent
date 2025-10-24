"""
Test the full analyst pipeline:
4 agents -> Meta-Agent -> Risk Committee

This tests the complete recommendation flow.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.technical_agent import get_technical_agent
from agents.fundamental_agent import get_fundamental_agent
from agents.sentiment_agent import get_sentiment_agent
from agents.risk_agent import get_risk_agent
from agents.meta_agent import get_meta_agent
from agents.risk_committee import get_risk_committee

def test_full_pipeline(ticker: str = "APLD"):
    """Test the complete analyst pipeline"""

    print("=" * 80)
    print(f"FULL ANALYST PIPELINE TEST - {ticker}")
    print("=" * 80)

    # Mock portfolio context
    portfolio_context = {
        "total_value": 1000,
        "cash": 200,
        "positions": [
            {"ticker": "APLD", "market_value": 200, "qty": 7},
            {"ticker": "NTLA", "market_value": 200, "qty": 8},
            {"ticker": "CRWV", "market_value": 150, "qty": 0.77},
            {"ticker": "SOUN", "market_value": 150, "qty": 10},
            {"ticker": "UUUU", "market_value": 100, "qty": 7.7},
        ]
    }

    print("\n" + "=" * 80)
    print("STEP 1: RUN 4 ANALYST AGENTS")
    print("=" * 80)

    # Initialize agents
    technical_agent = get_technical_agent()
    fundamental_agent = get_fundamental_agent()
    sentiment_agent = get_sentiment_agent()
    risk_agent = get_risk_agent()
    meta_agent = get_meta_agent()
    risk_committee = get_risk_committee()

    # Run each agent
    agent_recommendations = []

    print("\n[1/4] Technical Agent...")
    tech_result = technical_agent.analyze(ticker, portfolio_context)
    agent_recommendations.append(tech_result)
    print(f"  Action: {tech_result['action']}")
    print(f"  Confidence: {tech_result['confidence']}%")
    print(f"  Reasoning: {tech_result['reasoning']}")

    print("\n[2/4] Fundamental Agent...")
    fund_result = fundamental_agent.analyze(ticker, portfolio_context)
    agent_recommendations.append(fund_result)
    print(f"  Action: {fund_result['action']}")
    print(f"  Confidence: {fund_result['confidence']}%")
    print(f"  Reasoning: {fund_result['reasoning']}")

    print("\n[3/4] Sentiment Agent...")
    sent_result = sentiment_agent.analyze(ticker, portfolio_context)
    agent_recommendations.append(sent_result)
    print(f"  Action: {sent_result['action']}")
    print(f"  Confidence: {sent_result['confidence']}%")
    print(f"  Reasoning: {sent_result['reasoning']}")

    print("\n[4/4] Risk Agent...")
    risk_result = risk_agent.analyze(ticker, portfolio_context)
    agent_recommendations.append(risk_result)
    print(f"  Action: {risk_result['action']}")
    print(f"  Confidence: {risk_result['confidence']}%")
    print(f"  Reasoning: {risk_result['reasoning']}")

    print("\n" + "=" * 80)
    print("STEP 2: META-AGENT AGGREGATION (with diversity penalty)")
    print("=" * 80)

    meta_result = meta_agent.aggregate_recommendations(agent_recommendations, portfolio_context)

    print(f"\nConsensus Action: {meta_result['action']}")
    print(f"Base Confidence: {meta_result.get('base_confidence', 'N/A')}%")
    print(f"Final Confidence: {meta_result['confidence']}% (after diversity adjustment)")
    print(f"Diversity Score: {meta_result.get('diversity_score', 0):.2f}")
    print(f"Warning: {meta_result.get('warning', 'N/A')}")
    print(f"\nMeta-Analysis:")
    print(f"  {meta_result.get('meta_analysis', 'N/A')}")

    print("\n" + "=" * 80)
    print("STEP 3: RISK COMMITTEE POSITION SIZING")
    print("=" * 80)

    if meta_result['action'] in ["BUY", "SELL"]:
        # Build recommendation for Risk Committee
        recommendation = {
            "ticker": ticker,
            "action": meta_result['action'],
            "qty": 5,  # Default quantity
            "target_price": tech_result.get('signals', {}).get('price', 0),
            "confidence": meta_result['confidence'] / 100,
            "reasoning": meta_result.get('meta_analysis', '')
        }

        print(f"\nDebating position sizing for: {meta_result['action']} {ticker}")
        risk_debate = risk_committee.debate_position_sizing(recommendation, portfolio_context)

        print(f"\nOriginal: {meta_result['action']} 5 shares")
        print(f"Risk-Seeking: {risk_debate['proposals']['seeking']['proposed_qty']} shares")
        print(f"Risk-Neutral: {risk_debate['proposals']['neutral']['proposed_qty']} shares")
        print(f"Risk-Conservative: {risk_debate['proposals']['conservative']['proposed_qty']} shares")
        print(f"\nConsensus: {risk_debate['consensus']}")
        print(f"Stop Loss: {risk_debate.get('stop_loss', 'N/A')}")
        print(f"Winner: {risk_debate.get('winner', 'N/A')}")
        print(f"\nReasoning:")
        print(f"  {risk_debate.get('reasoning', 'N/A')}")
    else:
        print(f"\nAction is HOLD - no position sizing needed")

    print("\n" + "=" * 80)
    print("PIPELINE TEST COMPLETE")
    print("=" * 80)
    print("\nFull pipeline executed successfully:")
    print("  [OK] 4 Analyst Agents")
    print("  [OK] Meta-Agent Aggregation")
    print("  [OK] Risk Committee Debate")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Test with APLD
    test_full_pipeline("APLD")
