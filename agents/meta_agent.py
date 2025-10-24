"""
Meta Agent - Aggregates recommendations with diversity penalty

Prevents groupthink by penalizing unanimous agreement.
When all agents align, confidence is reduced to account for potential blind spots.
"""

import os
import sys
from typing import Dict, List, Optional
from collections import Counter

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MetaAgent:
    """
    Meta-level agent that aggregates recommendations from multiple agents.

    Key feature: Diversity penalty
    - High agreement (>80%) = potential groupthink → reduce confidence
    - Low agreement (<40%) = unclear signal → reduce confidence
    - Healthy disagreement (40-80%) = maintain confidence

    Philosophy: Skeptical when everyone agrees, skeptical when no one agrees.
    """

    def __init__(self):
        self.name = "meta_agent"

        # Diversity thresholds
        self.high_agreement_threshold = 0.80  # >80% agreement
        self.low_agreement_threshold = 0.40   # <40% agreement

        # Confidence penalties
        self.groupthink_penalty = 0.85        # Reduce by 15% for groupthink
        self.chaos_penalty = 0.90             # Reduce by 10% for chaos

    def aggregate_recommendations(
        self,
        agent_recs: List[Dict],
        portfolio_context: Optional[Dict] = None
    ) -> Dict:
        """
        Aggregate multiple agent recommendations with diversity scoring.

        Args:
            agent_recs: List of recommendation dicts from different agents
                Each dict should have:
                - action: str (BUY, SELL, HOLD, ADD)
                - confidence: float (0-1)
                - agent: str (agent name)
                - reasoning: str (optional)
            portfolio_context: Optional portfolio context

        Returns:
            Aggregated recommendation with diversity analysis
        """
        if not agent_recs:
            return {
                "action": "HOLD",
                "confidence": 0,
                "error": "No recommendations to aggregate"
            }

        # Extract actions and confidences
        actions = [rec["action"] for rec in agent_recs]
        confidences = [rec.get("confidence", 0.5) for rec in agent_recs]

        # Calculate agreement rate
        action_counts = Counter(actions)
        most_common_action = action_counts.most_common(1)[0][0]
        agreement_count = action_counts[most_common_action]
        agreement_rate = agreement_count / len(actions)

        # Calculate diversity score (inverse of agreement)
        diversity_score = 1 - agreement_rate

        # Determine diversity penalty and warning
        diversity_penalty, warning = self._calculate_diversity_penalty(
            agreement_rate,
            len(actions)
        )

        # Calculate base confidence (average)
        base_confidence = sum(confidences) / len(confidences)

        # Apply diversity adjustment
        final_confidence = base_confidence * diversity_penalty

        # Get agent breakdown
        agent_votes = {}
        for action in set(actions):
            count = actions.count(action)
            percentage = (count / len(actions)) * 100
            agents_for_action = [
                rec.get("agent", "unknown")
                for rec in agent_recs
                if rec["action"] == action
            ]
            agent_votes[action] = {
                "count": count,
                "percentage": percentage,
                "agents": agents_for_action
            }

        # Build result
        result = {
            "action": most_common_action,
            "confidence": final_confidence,
            "base_confidence": base_confidence,
            "diversity_score": diversity_score,
            "agreement_rate": agreement_rate,
            "diversity_penalty": diversity_penalty,
            "warning": warning,
            "agent_votes": agent_votes,
            "total_agents": len(actions),
            "meta_analysis": self._generate_analysis(
                agreement_rate,
                diversity_score,
                most_common_action,
                agent_votes
            )
        }

        return result

    def _calculate_diversity_penalty(
        self,
        agreement_rate: float,
        num_agents: int
    ) -> tuple[float, str]:
        """
        Calculate diversity penalty and generate warning.

        Returns:
            (penalty_multiplier, warning_message)
        """
        if agreement_rate >= self.high_agreement_threshold:
            # High agreement = potential groupthink
            return (
                self.groupthink_penalty,
                "[!] HIGH AGREEMENT: All agents aligned - potential groupthink. Confidence reduced by 15%."
            )
        elif agreement_rate <= self.low_agreement_threshold and num_agents >= 3:
            # Too much chaos (only penalize if 3+ agents)
            return (
                self.chaos_penalty,
                "[!] LOW AGREEMENT: Agents strongly disagree - unclear signal. Confidence reduced by 10%."
            )
        else:
            # Healthy disagreement
            return (
                1.0,
                "[OK] Healthy diversity: Agents show reasonable disagreement. No penalty applied."
            )

    def _generate_analysis(
        self,
        agreement_rate: float,
        diversity_score: float,
        consensus_action: str,
        agent_votes: Dict
    ) -> str:
        """Generate human-readable meta-analysis."""

        # Agreement level description
        if agreement_rate >= 0.90:
            agreement_desc = "unanimous"
        elif agreement_rate >= 0.70:
            agreement_desc = "strong"
        elif agreement_rate >= 0.50:
            agreement_desc = "moderate"
        else:
            agreement_desc = "weak"

        # Build analysis
        vote_breakdown = ", ".join([
            f"{action}: {data['count']} votes ({data['percentage']:.0f}%)"
            for action, data in agent_votes.items()
        ])

        analysis = f"{agreement_desc.capitalize()} consensus for {consensus_action}. "
        analysis += f"Vote breakdown: {vote_breakdown}. "

        if agreement_rate >= 0.80:
            analysis += "Caution: High agreement may indicate groupthink or overlooked risks. "
        elif agreement_rate <= 0.40:
            analysis += "Caution: Low agreement suggests conflicting signals or high uncertainty. "
        else:
            analysis += "Healthy debate among agents suggests well-considered position. "

        return analysis


# Singleton instance
_meta_agent_instance = None

def get_meta_agent() -> MetaAgent:
    """Get or create singleton MetaAgent instance."""
    global _meta_agent_instance
    if _meta_agent_instance is None:
        _meta_agent_instance = MetaAgent()
    return _meta_agent_instance


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("META AGENT - DIVERSITY PENALTY TESTING")
    print("=" * 80)
    print()

    meta = get_meta_agent()

    # Test Case 1: High Agreement (Groupthink)
    print("TEST 1: High Agreement (Potential Groupthink)")
    print("-" * 80)
    high_agreement = [
        {"action": "SELL", "confidence": 0.85, "agent": "technical"},
        {"action": "SELL", "confidence": 0.80, "agent": "risk"},
        {"action": "SELL", "confidence": 0.90, "agent": "momentum"},
        {"action": "SELL", "confidence": 0.82, "agent": "fundamental"}
    ]

    result1 = meta.aggregate_recommendations(high_agreement)
    print(f"Action: {result1['action']}")
    print(f"Base Confidence: {result1['base_confidence']:.1%}")
    print(f"Final Confidence: {result1['confidence']:.1%}")
    print(f"Agreement Rate: {result1['agreement_rate']:.1%}")
    print(f"Diversity Score: {result1['diversity_score']:.1%}")
    print(f"Penalty Applied: {result1['diversity_penalty']:.1%}")
    print(f"Warning: {result1['warning']}")
    print(f"Analysis: {result1['meta_analysis']}")
    print()

    # Test Case 2: Healthy Disagreement
    print("TEST 2: Healthy Disagreement")
    print("-" * 80)
    healthy_disagreement = [
        {"action": "HOLD", "confidence": 0.75, "agent": "technical"},
        {"action": "SELL", "confidence": 0.70, "agent": "risk"},
        {"action": "HOLD", "confidence": 0.80, "agent": "momentum"},
        {"action": "BUY", "confidence": 0.65, "agent": "fundamental"}
    ]

    result2 = meta.aggregate_recommendations(healthy_disagreement)
    print(f"Action: {result2['action']}")
    print(f"Base Confidence: {result2['base_confidence']:.1%}")
    print(f"Final Confidence: {result2['confidence']:.1%}")
    print(f"Agreement Rate: {result2['agreement_rate']:.1%}")
    print(f"Diversity Score: {result2['diversity_score']:.1%}")
    print(f"Penalty Applied: {result2['diversity_penalty']:.1%}")
    print(f"Warning: {result2['warning']}")
    print(f"Analysis: {result2['meta_analysis']}")
    print()

    # Test Case 3: Low Agreement (Chaos)
    print("TEST 3: Low Agreement (Chaos)")
    print("-" * 80)
    low_agreement = [
        {"action": "BUY", "confidence": 0.60, "agent": "technical"},
        {"action": "SELL", "confidence": 0.65, "agent": "risk"},
        {"action": "HOLD", "confidence": 0.70, "agent": "momentum"},
        {"action": "ADD", "confidence": 0.55, "agent": "fundamental"}
    ]

    result3 = meta.aggregate_recommendations(low_agreement)
    print(f"Action: {result3['action']}")
    print(f"Base Confidence: {result3['base_confidence']:.1%}")
    print(f"Final Confidence: {result3['confidence']:.1%}")
    print(f"Agreement Rate: {result3['agreement_rate']:.1%}")
    print(f"Diversity Score: {result3['diversity_score']:.1%}")
    print(f"Penalty Applied: {result3['diversity_penalty']:.1%}")
    print(f"Warning: {result3['warning']}")
    print(f"Analysis: {result3['meta_analysis']}")
    print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("High Agreement: Confidence reduced from 84.2% -> 71.6% (-15%)")
    print("Healthy Debate:  Confidence maintained at 72.5% (no penalty)")
    print("Low Agreement:  Confidence reduced from 62.5% -> 56.2% (-10%)")
    print()
    print("Meta-Agent successfully penalizes extremes (groupthink and chaos)")
    print("while rewarding healthy disagreement among agents.")
    print("=" * 80)
