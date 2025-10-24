# Risk Management Integration - Summary

## Overview

Integrated Risk Committee and Meta-Agent into the recommendation pipeline to:
1. Debate position sizing for every BUY/SELL recommendation
2. Penalize groupthink when all agents agree
3. Provide balanced, risk-adjusted trading decisions

## Components Built

### 1. Risk Committee (`agents/risk_committee.py`)
- **Three agents**: Risk-Seeking, Risk-Neutral, Risk-Conservative
- **Claude API**: Conducts authentic multi-agent debates
- **Output**: Consensus position size + stop loss + reasoning
- **Tracking**: Win rates, historical decisions

### 2. Meta-Agent (`agents/meta_agent.py`)
- **Diversity Penalty**: Reduces confidence when all agents agree (>80%)
- **Chaos Penalty**: Reduces confidence when no consensus (<40%)
- **Healthy Debate**: Maintains confidence for 40-80% agreement
- **Analysis**: Provides meta-level commentary on agent consensus

### 3. API Integration (`api/services.py`, `api/main.py`)
- **New Parameter**: `apply_risk=true` on `/api/recommendations`
- **Pipeline**: Base recommendation -> Risk Committee -> Risk-adjusted output
- **Automatic**: Optional integration, doesn't break existing flow

## How It Works

### Without Risk Integration (Default)
```
GET /api/recommendations

Response:
{
  "ticker": "APLD",
  "action": "ADD",
  "qty": 2,
  "confidence": 0.78,
  "reasoning": "Biotech momentum play..."
}
```

### With Risk Integration
```
GET /api/recommendations?apply_risk=true

Response:
{
  "ticker": "APLD",
  "action": "ADD",
  "qty": 4,  # Risk-adjusted from Risk Committee
  "confidence": 0.78,
  "reasoning": "Biotech momentum play...

[Risk Committee] 15% position balances high conviction with sector concentration risk. 
Risk-Seeking proposed 8 shares, Risk-Conservative proposed 3 shares. Consensus: 4 shares."
}
```

## Test Results

### Meta-Agent Diversity Penalty

**Test 1: High Agreement (Groupthink)**
- All 4 agents vote SELL
- Base confidence: 84.2%
- Final confidence: 71.6% (-15% penalty)
- Warning: "[!] HIGH AGREEMENT: potential groupthink"

**Test 2: Healthy Disagreement**
- 2 HOLD, 1 SELL, 1 BUY
- Base confidence: 72.5%
- Final confidence: 72.5% (no penalty)
- Warning: "[OK] Healthy diversity"

**Test 3: Low Agreement (Chaos)**
- All agents disagree (4 different votes)
- Base confidence: 62.5%
- Final confidence: 56.2% (-10% penalty)
- Warning: "[!] LOW AGREEMENT: unclear signal"

### Risk Committee Debate

**Input:**
- BUY 5 APLD @ $36.28 (85% confidence)

**Agent Proposals:**
- Risk-Seeking: 8 shares (30% position)
- Risk-Neutral: 4 shares (18% position)
- Risk-Conservative: 3 shares (12% position)

**Claude Consensus:**
- 4 shares
- Stop loss: $31.93 (-12%)
- Winner: Risk-Neutral
- Reasoning: "15% position balances high conviction with sector concentration risk"

## API Endpoints

### Get Recommendations (with Risk)
```bash
curl "http://localhost:8000/api/recommendations?apply_risk=true"
```

### Get Recommendations (without Risk)
```bash
curl "http://localhost:8000/api/recommendations"
```

## Integration Points

### 1. Recommendation Service
```python
from api.services import recommendation_service

# Without risk
recs = await recommendation_service.get_recommendations()

# With risk
recs_with_risk = await recommendation_service.get_recommendations(apply_risk=True)
```

### 2. Direct Risk Committee Usage
```python
from agents.risk_committee import get_risk_committee

committee = get_risk_committee()

result = committee.debate_position_sizing(
    recommendation={
        "ticker": "APLD",
        "action": "BUY",
        "qty": 5,
        "target_price": 36.28,
        "confidence": 0.85,
        "reasoning": "Strong momentum..."
    }
)

print(f"Consensus: {result['consensus']}")
print(f"Winner: {result['winner']}")
```

### 3. Direct Meta-Agent Usage
```python
from agents.meta_agent import get_meta_agent

meta = get_meta_agent()

result = meta.aggregate_recommendations([
    {"action": "SELL", "confidence": 0.85, "agent": "technical"},
    {"action": "SELL", "confidence": 0.80, "agent": "risk"},
    {"action": "HOLD", "confidence": 0.70, "agent": "fundamental"}
])

print(f"Consensus: {result['action']}")
print(f"Adjusted Confidence: {result['confidence']}")
print(f"Warning: {result['warning']}")
```

## Files Created/Modified

### Created:
- `agents/risk_committee.py` (700+ lines)
- `agents/meta_agent.py` (290 lines)
- `RISK_COMMITTEE_README.md`
- `RISK_INTEGRATION_SUMMARY.md` (this file)

### Modified:
- `api/services.py` - Added Risk Committee integration
- `api/main.py` - Added `apply_risk` parameter

## Benefits

### 1. Position Sizing Automation
- No more guessing "how much to buy"
- Three risk perspectives debate every position
- Explicit stop losses provided

### 2. Groupthink Detection
- System is skeptical when everyone agrees
- Confidence reduced when consensus is too high
- Prevents overconfidence bias

### 3. Balanced Risk Management
- Risk-Seeking pushes for size
- Risk-Conservative advocates caution
- Risk-Neutral finds middle ground
- Claude mediates debate

### 4. Historical Tracking
- See which agent wins over time
- Analyze if system is too aggressive/conservative
- Adjust weights based on performance

## Example Workflow

```
1. Agent generates recommendation
   -> "BUY APLD at $36.28, confidence 85%"

2. Risk Committee debates
   -> Risk-Seeking: "30% position!"
   -> Risk-Conservative: "12% max, we're overexposed"
   -> Risk-Neutral: "18% standard sizing"
   -> Claude: "15% balances conviction and concentration risk"

3. Meta-Agent checks diversity
   -> 2 agents want BUY, 1 wants HOLD
   -> Agreement: 66% (healthy)
   -> No penalty applied

4. Final recommendation
   -> BUY 4 shares APLD at $36.28
   -> Stop loss: $31.93 (-12%)
   -> Confidence: 85% (maintained)
   -> Reasoning: Includes debate summary
```

## Future Enhancements

- [ ] Add 4th agent: Risk-Adaptive (changes with market regime)
- [ ] Track actual trade outcomes vs agent recommendations
- [ ] Machine learning to optimize agent weights
- [ ] Real-time portfolio context in debates
- [ ] Dashboard visualization of debates
- [ ] Email/webhook notifications when high-conviction trades debated

## Status

✅ **COMPLETE** - Risk management system integrated

- Risk Committee operational (3 agents)
- Meta-Agent operational (diversity penalty)
- API integration complete
- Tested and verified
- Ready for production use

**Bottom line**: Every recommendation can now be risk-adjusted through multi-agent debate with groupthink detection.
