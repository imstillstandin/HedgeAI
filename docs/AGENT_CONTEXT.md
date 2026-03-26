FX Risk Radar — Agent Context
Purpose of This Document
This document provides the core context and philosophy behind FX Risk Radar so that AI coding agents working on the repository understand:
the product vision
the problem being solved
the behavioural insights behind the design
the risk calculation logic
the user experience principles
the long-term strategic direction
All development work should align with these principles.
Product Overview
FX Risk Radar is a foreign exchange risk monitoring platform designed for small and medium-sized businesses (SMEs) that trade internationally.
The platform helps businesses:
identify foreign currency exposure
quantify potential financial impact from FX movements
receive simple guidance on risk mitigation
monitor currency markets continuously
FX Risk Radar acts as a digital FX risk manager for SMEs.
The product is intentionally designed to translate complex FX market dynamics into clear business insights.
The Core Problem
SMEs engaged in international trade often have significant FX exposure but do not actively manage currency risk.
Common characteristics:
Most SMEs convert currency only when payments are due
Hedging tools are perceived as complex
FX risk is rarely quantified
Businesses often react only after negative currency moves
Research indicates that 80–95% of SMEs do not hedge FX exposure.
This leaves businesses vulnerable to exchange rate volatility.
Market Gap
There is currently a missing layer between:
Accounting systems (Xero, QuickBooks, MYOB)
and
FX execution providers (banks, brokers, payment platforms)
Accounting software tracks invoices but does not analyse currency risk.
FX providers execute transactions but do not continuously monitor SME exposure.
FX Risk Radar fills this gap by acting as the decision layer between business data and the FX market.
Product Philosophy
FX Risk Radar should focus on decision support, not market prediction.
The goal is to help SMEs answer three questions:
What is my FX exposure?
What is the financial risk?
What should I consider doing?
All system outputs should support answering these questions clearly.
Key Concept: Profit at Risk
SME users do not think in exchange rates.
They think in:
profit
margin
cash flow
Therefore the platform should prioritise profit-at-risk calculations.
Example:
Copy code

USD Payable: 275,000
Exchange Rate: 0.66

AUD value = 416,667
If AUD weakens 5%

New value = 438,433

Additional cost = $21,766
The platform should surface insights like:
"A 5% currency move could increase your cost by $21,766."
This mirrors the conversations experienced FX dealers have with SME clients.
Behavioural Insights (SME Psychology)
FX Risk Radar is designed based on real behavioural patterns observed in SME FX clients.
Important observations include:
SMEs prefer avoiding bad rates rather than achieving the best rate.
Risk avoidance drives decisions more than optimisation.
Psychological exchange rate levels trigger activity.
Examples include:
AUD/USD
0.70
0.72
0.75
AUD/GBP
0.55
When these levels are reached, SMEs frequently contact brokers.
Settlement proximity affects decision making.
The closer a payment is to settlement:
the less likely businesses are to hedge
the more they hope the market improves
Regret strongly influences behaviour.
Many SMEs regret missing favourable FX levels.
Example:
"I should have locked that rate."
This emotional dynamic should inform alert design.
Most SMEs do not use hedging tools.
Common reasons include:
perceived complexity
lack of explanation
misunderstanding margin requirements
The platform must simplify these concepts.
Core Features
Exposure Detection
FX Risk Radar identifies foreign currency exposure from:
accounting integrations
CSV imports
manual entry
Detected exposures include:
currency
amount
settlement timing
payable vs receivable
Scenario Analysis
Standard FX risk scenarios include:
3% move
5% move
10% move
These scenarios estimate potential financial impact.
FX Health Score
The FX Health Score measures overall FX risk management quality.
The score ranges from 0–100.
Factors influencing the score include:
exposure size
settlement timing
concentration risk
hedging coverage
The score provides a simple indicator of risk management effectiveness.
Exposure Timeline
FX exposures should be visualised across time.
Example buckets:
0–30 days
30–60 days
60–90 days
This allows SMEs to see their currency risk pipeline.
Alert System
Alerts should focus on high-signal events.
Examples include:
psychological FX levels
large unhedged exposures
settlement windows approaching
volatility events (CPI, payrolls, FOMC)
Alerts should prioritise relevance and avoid excessive notifications.
UX Principles
The interface should prioritise clarity.
The dashboard should immediately communicate:
FX exposure
Profit at risk
Next settlement risk
Suggested actions
Avoid financial jargon where possible.
Information should be translated into plain business impact.
Long-Term Product Vision
FX Risk Radar should evolve into a continuous FX monitoring platform for SMEs.
Future capabilities may include:
automated exposure detection
recurring exposure forecasting
risk alerts
broker connectivity
execution workflows
portfolio analytics
The platform could ultimately function as an SME treasury management layer.
Large corporations already use treasury systems for this purpose.
SMEs typically do not.
Strategic Advantage
FX Risk Radar’s key differentiation comes from domain expertise rather than technology alone.
Important advantages include:
real-world FX dealer insights
SME behavioural understanding
simplified risk framing
practical hedging guidance
These insights are difficult to replicate.
Development Principles
All development should follow these guidelines:
keep risk calculations separate from UI logic
prioritise simplicity over complexity
translate FX markets into business impact
focus on actionable insights
minimise unnecessary alerts
The goal is not to build a trading platform but to build a risk intelligence system for SMEs.
Final Perspective
FX Risk Radar is not merely an FX calculator.
It is designed to become the decision layer between SMEs and the foreign exchange market.
If executed well, it can become an essential financial infrastructure tool for internationally trading businesses
