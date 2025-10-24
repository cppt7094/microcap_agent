"""
Test script for Core Directives System (Brutal Honesty Framework)
"""

from agents.core_directives import (
    get_agent_directive,
    get_scoring_guidelines,
    validate_recommendation_quality,
    EXAMPLE_GOOD_RECOMMENDATIONS,
    EXAMPLE_BAD_RECOMMENDATIONS
)

print("=" * 80)
print("CORE DIRECTIVES SYSTEM TEST")
print("=" * 80)

# Test 1: Get Scanner Directive
print("\n1. SCANNER DIRECTIVE (truncated)")
print("-" * 80)
scanner_directive = get_agent_directive("scanner")
print(f"Length: {len(scanner_directive)} characters")
print("First line contains core directives...")

# Test 2: Get Risk Manager Directive
print("\n2. RISK MANAGER DIRECTIVE (truncated)")
print("-" * 80)
risk_directive = get_agent_directive("risk")
print(f"Length: {len(risk_directive)} characters")
# Check for key phrases
if "position sizing" in risk_directive.lower():
    print("[OK] Contains position sizing guidance")
if "cut losers" in risk_directive.lower():
    print("[OK] Contains loss-cutting directive")
if "capital preservation" in risk_directive.lower():
    print("[OK] Contains capital preservation principle")

# Test 3: Scoring Guidelines
print("\n3. SCORING GUIDELINES")
print("-" * 80)
guidelines = get_scoring_guidelines()
for score_range, meaning in guidelines["ranges"].items():
    print(f"  {score_range:8} - {meaning}")

print(f"\nPhilosophy: {guidelines['philosophy'][:100]}...")

# Test 4: Validate Good Recommendations
print("\n4. VALIDATING GOOD RECOMMENDATIONS")
print("-" * 80)
for i, rec in enumerate(EXAMPLE_GOOD_RECOMMENDATIONS[:3], 1):
    print(f"\nGood Example {i}:")
    print(f"  Text: {rec[:60]}...")
    validation = validate_recommendation_quality(rec)
    print(f"  Valid: {validation['valid']}")
    print(f"  Has Data: {validation['has_data']}")
    print(f"  Word Count: {validation['word_count']}")
    if validation['issues']:
        print(f"  Issues: {validation['issues']}")

# Test 5: Validate Bad Recommendations
print("\n5. VALIDATING BAD RECOMMENDATIONS")
print("-" * 80)
for i, rec in enumerate(EXAMPLE_BAD_RECOMMENDATIONS[:3], 1):
    print(f"\nBad Example {i}:")
    print(f"  Text: {rec[:60]}...")
    validation = validate_recommendation_quality(rec)
    print(f"  Valid: {validation['valid']}")
    print(f"  Issues: {', '.join(validation['issues'])}")
    print(f"  Suggestion: {validation['suggestion']}")

# Test 6: Compare Directive Types
print("\n6. DIRECTIVE COMPARISON")
print("-" * 80)
directive_types = ["risk", "technical", "fundamental", "scanner", "news"]
for dtype in directive_types:
    directive = get_agent_directive(dtype)
    print(f"{dtype.upper():12} - {len(directive):,} chars")

# Test 7: Check for Key Phrases in Core Directives
print("\n7. CORE DIRECTIVE CONTENT CHECK")
print("-" * 80)
core_directive = get_agent_directive()  # No type = core only
key_phrases = [
    ("NO SYCOPHANCY", "Anti-sycophancy rules"),
    ("BE DIRECT", "Direct communication"),
    ("CONVICTION", "Conviction levels"),
    ("CHALLENGE", "Challenging user"),
    ("HARSH", "Harsh scoring"),
    ("ACTIONABLE", "Actionability focus")
]

for phrase, description in key_phrases:
    if phrase in core_directive:
        print(f"  [OK] {description}")
    else:
        print(f"  [MISSING] {description}")

# Test 8: Custom Recommendation Validation
print("\n8. CUSTOM RECOMMENDATION TEST")
print("-" * 80)

test_recommendations = [
    "BUY TSLA at $180. Breaking resistance on volume. Target $220.",
    "This stock might potentially be worth considering if conditions remain favorable...",
    "SELL - High conviction. Down 15%, trend broken. Cut your loss.",
]

for i, rec in enumerate(test_recommendations, 1):
    print(f"\nTest {i}: {rec[:50]}...")
    validation = validate_recommendation_quality(rec)
    print(f"  Result: {'PASS' if validation['valid'] else 'FAIL'}")
    if not validation['valid']:
        print(f"  Issues: {', '.join(validation['issues'])}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

print("\nKEY TAKEAWAYS:")
print("- Directives enforce brutal honesty over sycophancy")
print("- Harsh scoring makes high scores meaningful (85+ is rare)")
print("- Validation catches hedging language and forces directness")
print("- Agent-specific augmentations tailor behavior to role")
print("- System prioritizes actionability over verbosity")
