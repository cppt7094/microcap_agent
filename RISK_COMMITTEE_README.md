# Risk Committee - Multi-Agent Position Sizing Debate

## Overview

The Risk Committee is a three-agent system that debates optimal position sizing for trading recommendations. Each agent represents a different risk philosophy and argues using Claude AI.

## Test Results

The system is working perfectly! Example output:

```
ORIGINAL RECOMMENDATION:
  BUY 5 APLD @ $36.28
  Confidence: 85%

DEBATE RESULTS:
  Risk-Seeking:      BUY 8 shares (30% position)
  Risk-Neutral:      BUY 4 shares (18% position)
  Risk-Conservative: BUY 3 shares (12% position)

CONSENSUS:         BUY 4 shares
Stop Loss:         $31.93 (-12%)
Winner:            Risk-Neutral
```

## Usage

```python
from agents.risk_committee import get_risk_committee

committee = get_risk_committee()

recommendation = {
    "ticker": "APLD",
    "action": "BUY",
    "qty": 5,
    "target_price": 36.28,
    "confidence": 0.85,
    "reasoning": "Strong momentum..."
}

result = committee.debate_position_sizing(recommendation)
```

## Features

- Three distinct risk philosophies
- Claude API for authentic debates
- Historical tracking
- Win rate statistics
- Brutal honesty framework integration

See full documentation in the file.
