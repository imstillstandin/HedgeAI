SME FX Behaviour Engine
Purpose
This document captures observed behavioural patterns of SME clients dealing with foreign exchange exposure.
These insights should guide:
alert design
hedging suggestions
dashboard messaging
risk calculations
product UX
The goal is to replicate the thinking process of an experienced FX dealer advising SME clients.
Core Behaviour Insights
1. Most SMEs Do Not Actively Hedge
The majority of SMEs engaged in international trade do not use formal FX hedging strategies.
Key findings:
Over 80% of SMEs have never traded FX options
Over 40% have never traded FX forwards �
Inside Small Business +1
Many SMEs simply convert currency at the spot rate when payments are due
Reasons include:
lack of awareness
perceived complexity
limited financial expertise
absence of guidance from banks or brokers
Implication for the platform:
The system must identify exposure automatically and translate FX movements into clear business impact.
2. SMEs Think in Profit and Cash Flow, Not FX Rates
Most SME owners do not interpret exchange rates directly.
They think in terms of:
profit
costs
margin
cash flow
Example:
Instead of showing:
Copy code

AUDUSD = 0.6623
The system should show:
Copy code

If AUD weakens 5%
your next USD payment could cost

$18,400 more
This framing dramatically improves comprehension and engagement.
3. Avoiding Bad Rates Matters More Than Getting the Best Rate
SMEs generally prioritize risk reduction over rate optimization.
Typical mindset:
“I just don’t want the market to move against me.”
This means:
hedging decisions are often driven by fear of adverse moves
perfect timing is not required
Implication:
The platform should emphasize risk protection rather than market prediction.
4. Psychological FX Levels Trigger Client Activity
Certain FX levels often trigger a surge in hedging or trading activity.
Examples:
Copy code

AUD/USD
0.70
0.72
0.75

AUD/GBP
0.55
When these levels are reached:
SME clients frequently contact brokers
hedging discussions increase
deal flow accelerates
Implication:
The alert engine should monitor psychological FX levels.
5. Settlement Timing Influences Risk Behaviour
SME hedging behaviour changes depending on how close a payment is to settlement.
Typical pattern:
Early in the exposure timeline
→ more open to hedging discussions
Close to settlement
→ clients often hope the market improves
This behaviour increases risk.
Implication:
The platform should highlight risk earlier in the exposure timeline.
6. Regret Drives Future Hedging Decisions
SMEs frequently regret missing favourable FX levels.
Example:
Client waits for a better rate.
Market moves against them.
Typical reaction:
“I should have locked that rate earlier.”
Implication:
Alerts and insights should include recent market context.
Example:
Copy code

AUD/USD recently traded at 0.70
This reinforces decision awareness.
7. Partial Hedging Is the Most Common Starting Point
SMEs rarely hedge 100% of exposure initially.
Typical behaviour:
hedge 30–50%
leave the remainder open
Reasons:
desire for flexibility
uncertainty about market direction
fear of opportunity cost
Implication:
The system should recommend hedge ranges, not fixed percentages.
Example:
Copy code

Suggested hedge range
40% – 60%
8. Operational Friction Discourages Broker Switching
Many SMEs stay with suboptimal FX providers because switching is inconvenient.
Key friction points:
beneficiary details must be re-entered
payment history is lost
operational disruption
Implication:
FX Risk Radar should focus on decision support rather than forcing provider switching.
9. Most SMEs Discover FX Costs After Payment
Many businesses only discover the real FX cost after an invoice is paid.
In some markets over half of businesses only see the true FX cost after settlement �.
PYMNTS.com
Implication:
The platform must highlight FX risk before settlement.
10. Recurring Exposure Patterns Are Common
Many SMEs have consistent FX patterns.
Examples:
monthly supplier payments
quarterly inventory purchases
recurring export receipts
Implication:
The system should detect recurring patterns such as:
Copy code

Typical monthly USD exposure
$90k – $120k
This enables forecasting of future FX needs.
Behavioural Design Principles
The SME behaviour engine should follow these principles.
Translate FX Into Business Impact
Always express risk in monetary terms.
Provide Clear Suggested Actions
Users should always understand the next step.
Example:
Copy code

Consider hedging 40–60% of this exposure.
Avoid Alert Fatigue
Alerts should only trigger for:
currencies the business uses
meaningful exposure thresholds
major market events
Reinforce Positive Behaviour
When users reduce risk, show positive feedback.
Example:
Copy code

FX Risk Reduced
Your hedge reduced profit at risk by $8,400
Strategic Importance
The SME behaviour engine is a core competitive advantage for FX Risk Radar.
Most FX tools are built around:
Copy code

market data
+ financial models
FX Risk Radar instead combines:
Copy code

market data
+ behavioural insights
+ risk calculations
This allows the platform to behave like an experienced FX advisor rather than a simple calculator.
Key Takeaway
SMEs do not need complex trading tools.
They need a system that helps them answer three questions:
Copy code

What is my FX exposure?
What is the financial risk?
What should I consider doing?
FX Risk Radar exists to provide these answers continuously
