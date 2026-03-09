FX Risk Radar — System Architecture
Purpose
This document defines the recommended system architecture for FX Risk Radar.
It is intended to help:
AI coding agents
developers
future collaborators
understand how the platform should be structured as it grows from a Streamlit prototype into a full SaaS product.
The architecture should support the product evolving from:
Text
Copy code
manual calculator
→ exposure dashboard
→ monitoring platform
→ broker-connected decision layer
The most important architectural principle is:
keep business logic separate from UI logic
System Overview
FX Risk Radar should be built as a modular platform with distinct layers.
At a high level:
Text
Copy code
Data Input Layer
        ↓
Exposure Engine
        ↓
Risk Engine
        ↓
Alert Engine
        ↓
Action / Execution Layer
        ↓
Frontend / Dashboard
Each layer has a separate responsibility.
1. Data Input Layer
Role
The input layer ingests data from multiple sources and converts it into a standard internal structure.
Supported Inputs
Initial inputs:
manual user entry
CSV upload
Future inputs:
Xero
QuickBooks
MYOB
broker transaction feeds
historical FX conversion exports
Required Standard Fields
All inputs should be transformed into a common exposure record format.
Example fields:
Text
Copy code
source_system
source_id
counterparty
currency
amount
type
due_date
rate
status
beneficiary
created_at
Design Principle
The rest of the platform should not care where the data came from.
CSV, manual input, and accounting APIs should all become the same normalized object internally.
2. Exposure Engine
Role
The exposure engine is responsible for identifying and aggregating FX exposure.
It answers questions like:
what currencies is the business exposed to?
how much is exposed?
when are settlements due?
where is the greatest concentration of risk?
Responsibilities
The exposure engine should:
group exposures by currency
group exposures by payable vs receivable
calculate nearest due date
calculate total foreign amount
calculate AUD equivalent
detect concentration risk
detect recurring exposure patterns
build exposure timeline buckets
Example Output
Text
Copy code
USD payable
275,000
Due in 43 days
AUD equivalent
416,667
Time Buckets
The engine should support timeline grouping such as:
0–30 days
31–60 days
61–90 days
90+ days
This powers the exposure timeline view.
3. Risk Engine
Role
The risk engine translates exposure into business impact.
This is the core logic layer of FX Risk Radar and one of the main product moats.
Responsibilities
The risk engine should calculate:
AUD equivalent value
3% scenario impact
5% scenario impact
10% scenario impact
profit at risk
margin impact
suggested hedge ranges
FX health score
cost of inaction estimates
Core Principle
The output of the risk engine should be framed in business terms, not raw market terms.
Example:
Bad:
Text
Copy code
AUDUSD moved from 0.66 to 0.63
Good:
Text
Copy code
A 5% move in AUD could increase your cost by $21,766
Suggested Hedge Logic
Hedge suggestions should be based on:
exposure size
days to settlement
type of exposure
optional user-specific settings
Examples:
Large payable exposure due soon
→ stronger hedge suggestion
Small exposure far from settlement
→ lighter suggestion / monitor
Health Score
The FX Health Score should combine:
impact severity
settlement urgency
concentration risk
hedge coverage
volatility environment
The score should remain simple and interpretable.
4. Alert Engine
Role
The alert engine turns FX Risk Radar from a dashboard into an always-on monitoring system.
Responsibilities
The alert engine should monitor for:
psychological FX levels
settlement windows approaching
large unhedged exposures
sharp changes in exposure
major macro events
margin risk thresholds
new currencies appearing in the business
Alert Types
Psychological Level Alerts
Examples:
AUD/USD hits 0.70
AUD/GBP hits 0.55
These should trigger because they often drive SME action.
Settlement Risk Alerts
Examples:
large exposure due in 14 days
exposure still unhedged
Risk Threshold Alerts
Examples:
5% move now equals more than X AUD
margin impact exceeds tolerance
Event Alerts
Examples:
US CPI
FOMC
payrolls
These should only be sent when relevant to the customer’s active currencies.
Alert Design Principle
Alerts must prioritize signal over noise.
The platform should only alert on:
currencies the user actually uses
meaningful exposures
relevant market events
Too many alerts will destroy trust and engagement.
5. Action / Execution Layer
Role
This layer translates risk insights into next steps.
Initially it does not need to execute trades directly.
Early Responsibilities
generate hedge suggestions
generate broker-ready trade request summaries
export reports
support “connect accounting software”
support “discuss with FX provider” workflows
Future Responsibilities
broker integrations
quote requests
execution handoff
rate comparison
transaction routing
Strategic Position
FX Risk Radar should initially function as the decision layer, not the broker.
It sits between:
Text
Copy code
SME business
↓
FX Risk Radar
↓
broker / bank
↓
FX market
Execution can come later.
6. Frontend Layer
Role
The frontend displays the outputs of the system in a way SME users can understand quickly.
Current State
The current prototype is built in Streamlit.
That is acceptable for validation and early testing.
Future State
A production version may eventually use:
React / Next.js frontend
FastAPI backend
PostgreSQL database
scheduled background workers
UX Principles
The dashboard should answer three questions immediately:
What is my FX exposure?
What is my financial risk?
What should I consider doing?
Dashboard Priority
The top of the interface should always show:
total FX exposure
profit at risk
health score
next settlement
primary suggested action
Advanced detail should appear lower on the screen or inside expanders.
7. Persistence Layer
Role
Persistence is required once the system moves beyond temporary manual analysis.
Future Database Objects
Likely objects include:
users
organisations
connected_accounts
exposures
counterparties
beneficiaries
alert_preferences
market_alerts
hedge_actions
settings
historical_rates_cache
Recommended Database
Use PostgreSQL once the product moves beyond prototype stage.
8. Background Processing Layer
Role
Continuous monitoring requires scheduled jobs and asynchronous processing.
Responsibilities
refresh market rates
poll accounting integrations
recalculate exposure
evaluate alert rules
send notifications
update health scores
Why It Matters
Without background jobs, FX Risk Radar is just a static dashboard.
With background jobs, it becomes an always-on monitoring platform.
9. Market Data Layer
Role
This layer manages FX rate data and relevant market context.
Responsibilities
current spot rates
recent ranges
historical highs/lows
psychological level checks
event calendar support
Design Principle
Market data should be handled in one dedicated module, not scattered throughout the app.
This keeps risk calculations consistent.
Recommended Project Structure
A recommended project structure is:
Text
Copy code
fx-risk-radar/
│
├── app.py
├── requirements.txt
├── .gitignore
│
├── data/
│   └── sample_exposure.csv
│
├── core/
│   ├── exposure_engine.py
│   ├── risk_engine.py
│   ├── alert_engine.py
│   └── market_data.py
│
├── integrations/
│   ├── csv_loader.py
│   ├── manual_input.py
│   ├── xero_client.py
│   ├── quickbooks_client.py
│   └── myob_client.py
│
├── ui/
│   ├── summary_cards.py
│   ├── action_panel.py
│   ├── exposure_table.py
│   └── timeline_panel.py
│
├── utils/
│   ├── formatting.py
│   └── dates.py
│
└── docs/
    ├── AGENT_CONTEXT.md
    ├── PRODUCT_STRATEGY.md
    ├── SME_FX_BEHAVIOUR.md
    ├── HEDGING_LOGIC.md
    └── SYSTEM_ARCHITECTURE.md
Development Principles
1. Keep logic separate from presentation
Calculation logic must not live inside the UI wherever possible.
2. Keep modules focused
Each engine should do one job well.
3. Preserve business language
Outputs should always translate into business impact.
4. Build for evolution
Architecture should support:
manual input now
accounting integration later
monitoring later
execution later
5. Protect the moat
The moat is not the UI.
The moat is the combination of:
behavioural insights
risk logic
alert logic
decision framing
These should be documented and modularized carefully.
Recommended Build Sequence
Stage 1
Refactor current Streamlit prototype into modules.
Priority modules:
utils/formatting.py
core/exposure_engine.py
core/risk_engine.py
Stage 2
Add persistence and saved settings.
Stage 3
Add accounting integrations.
Stage 4
Add background jobs and alert engine.
Stage 5
Add broker connectivity / action workflows.
This order reduces rebuild risk.
Final Architectural Principle
FX Risk Radar should be built as an always-on decision system for SME FX risk, not just a one-time calculator.
Everything in the architecture should support this future state.
The system should ultimately behave like:
Text
Copy code
accounting data
↓
exposure detection
↓
risk analysis
↓
continuous monitoring
↓
timely action guidance
That is the architectural north star.
