"""
Test script for Opportunity Scanner Agent
"""

import logging
from agents.opportunity_scanner import OpportunityScannerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 80)
    print("Testing Opportunity Scanner Agent")
    print("=" * 80)

    # Initialize scanner
    scanner = OpportunityScannerAgent()

    # Run scan
    opportunities = scanner.scan_for_opportunities(max_results=10)

    print("\n" + "=" * 80)
    print(f"SCAN RESULTS: {len(opportunities)} Opportunities Found")
    print("=" * 80)

    if not opportunities:
        print("\nNo opportunities found matching criteria")
        return

    # Display results
    for i, opp in enumerate(opportunities, 1):
        print(f"\n{i}. {opp['ticker']} - Score: {opp['score']}/100")
        print(f"   Recommendation: {opp['recommendation']}")
        print(f"   Price: ${opp['price']:.2f} -> Target: ${opp['target_price']:.2f}")
        print(f"   Market Cap: ${opp['market_cap']:,.0f}")
        print(f"   Sector: {opp['sector']}")
        print(f"   Signals:")
        print(f"      - Momentum: {opp['signals']['momentum']}/25")
        print(f"      - Technical: {opp['signals']['technical']}/25")
        print(f"      - Fundamental: {opp['signals']['fundamental']}/25")
        print(f"      - Sentiment: {opp['signals']['sentiment']}/15")
        print(f"      - Sector Match: {opp['signals']['sector_match']}/15")
        print(f"   Reasoning: {opp['reasoning']}")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
