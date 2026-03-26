FX Risk Radar — Hedging Logic Engine
Purpose
This document defines the decision framework used by FX Risk Radar to generate hedging suggestions for SME users.
The logic combines:
quantitative exposure calculations
behavioural insights from SME FX users
risk management principles
timing considerations
research on SME FX adoption
The objective is not to predict FX markets, but to reduce business risk and protect margins.
Key Research Insights
Most SMEs Do Not Hedge
Multiple studies confirm that most SMEs do not actively manage FX risk.
Examples:
Over 80% of SMEs have never traded FX options
Over 40% have never used FX forwards
SMEs represent only ~14% of forward FX market activity despite large exposure levels �
Inside Small Business +1
Reasons include:
lack of product knowledge
perceived complexity
operational friction
absence of clear guidance
Implication:
The platform must act as a decision support system that simplifies hedging.
Core Hedging Philosophy
FX Risk Radar is built around one core idea:
Hedging protects margins, not market timing.
SME users should understand that hedging is about:
reducing uncertainty
protecting cashflow
stabilising profit margins
not maximizing FX gains.
Exposure Detection
All exposures must be classified as either:
Copy code

payable
receivable
Example:
Copy code

USD payable
180,000
Due in 45 days
The system calculates:
foreign currency amount
AUD equivalent value
settlement timeline
concentration risk
Scenario Risk Calculations
The risk engine evaluates FX movement scenarios.
Standard scenarios:
Copy code

3% currency move
5% currency move
10% currency move
Example:
Copy code

USD exposure: 200,000
AUDUSD rate: 0.66

AUD equivalent: 303,030

5% AUD weakness → cost increases by ~$15,150
These values must always be displayed in AUD impact terms, not FX rates.
Suggested Hedge Ranges
SMEs typically hedge part of their exposure, not all of it.
Common real-world behaviour:
Copy code

30–50% hedge coverage
This balances:
risk protection
flexibility if the market moves favourably
Suggested ranges:
Exposure Size
Days to Settlement
Hedge Suggestion
>100k
<60 days
40–60%
>50k
<90 days
20–40%
small exposure
>90 days
monitor
Receivables may have slightly lower hedge ratios.
Settlement Timeline Logic
Hedging urgency increases as settlement approaches.
Timeline logic:
Copy code

90+ days → monitor
60–90 days → evaluate hedge
30–60 days → partial hedge recommended
0–30 days → risk alert
Behavioural insight:
SMEs tend to delay hedging when settlement is near and hope for a favourable move.
The system should counteract this behaviour.
Profit at Risk Calculation
One of the most important outputs is:
Copy code

Profit at Risk
This represents the potential financial impact of a currency move.
Example:
Copy code

5% AUD move
Potential cost increase
$18,420
This framing improves decision-making dramatically.
FX Health Score
Each exposure receives a score.
Copy code

0 – 100
Factors:
size of exposure
settlement urgency
potential FX impact
concentration risk
Example:
Copy code

FX Health Score
72 / 100
Lower scores indicate greater risk.
Psychological FX Levels
SMEs often react strongly to certain FX levels.
Examples:
Copy code

AUDUSD
0.70
0.72
0.75

AUDGBP
0.55
These levels should trigger alerts.
Example:
Copy code

AUD/USD has reached 0.70
Many businesses hedge at this level.
Behaviour-Based Alerts
Alerts should trigger when:
Copy code

large exposure exists
settlement approaching
psychological levels reached
risk thresholds exceeded
major macro events approaching
Example:
Copy code

Your USD exposure could cost $22,000 more
if AUD weakens 5%
Macro Event Awareness
Certain economic releases frequently move FX markets.
Examples:
Copy code

FOMC meetings
US CPI
Nonfarm payrolls
RBA decisions
Alerts should only appear if relevant to the user's currencies.
Partial Hedging Strategy
SMEs rarely hedge 100% immediately.
Recommended pattern:
Copy code

Initial hedge
30–50%

Add hedge later if market improves
Example:
Copy code

USD payable
200,000

Initial hedge
80,000

Remaining exposure
120,000
This approach:
reduces downside risk
preserves flexibility
Positive Reinforcement
Users should receive feedback when good decisions reduce risk.
Example:
Copy code

Good decision.

Your hedge reduced FX risk by
$9,200
Positive reinforcement improves long-term engagement.
Alert Fatigue Prevention
The system must avoid excessive notifications.
Alerts should only trigger when:
Copy code

risk is meaningful
exposure is significant
market movement is relevant
Core User Questions
The system should continuously answer three questions:
Copy code

What is my FX exposure?
What is my financial risk?
What should I consider doing?
Key Strategic Insight
SME FX risk management is not a technology problem.
It is a communication problem.
Businesses already have access to hedging tools but struggle with:
understanding exposure
quantifying risk
deciding when to act
FX Risk Radar solves this by translating market movements into clear business impact.
Additional Insight From Research
Research also shows that:
68% of SMEs want guidance on managing FX volatility
57% say earlier FX risk management would have helped their business �
SME Today
This reinforces the core thesis behind FX Risk Radar.
Final Design Principle
The system should behave like an experienced FX advisor who constantly asks:
Copy code

Is this business exposed?
How big is the risk?
Should they consider acting now?
Every feature should support that objective.
