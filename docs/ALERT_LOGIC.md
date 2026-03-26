FX Risk Radar — Alert Logic Engine
Purpose
The Alert Engine transforms FX Risk Radar from a passive dashboard into an active monitoring system.
Instead of requiring SME owners to watch currency markets, the system continuously monitors:
FX market movements
business exposure
settlement timelines
macroeconomic events
When relevant conditions occur, the system provides clear and actionable alerts.
The objective is to notify users only when something meaningful happens.
Core Alert Principles
The alert system must follow these principles.
Relevance
Only alert on currencies the business actually uses.
Example:
If the business only trades in:
Copy code

USD
EUR
Then alerts for:
Copy code

AUDJPY
AUDCAD
should never be sent.
Financial Impact
Alerts should only trigger when FX movement could materially affect the business.
Example threshold:
Copy code

Potential impact > $3,000
This threshold may vary depending on exposure size.
Timing Sensitivity
As settlement dates approach, the system should become more proactive.
Example timeline logic:
Copy code

90+ days → monitoring alerts only
60–90 days → risk awareness alerts
30–60 days → hedge consideration alerts
0–30 days → urgent risk alerts
Signal Over Noise
Too many alerts will cause users to ignore the platform.
The system must prioritise quality alerts rather than quantity.
Alert Categories
FX Risk Radar should support multiple alert types.
1. Risk Threshold Alerts
These alerts trigger when FX movement could materially affect the business.
Example:
Copy code

USD Payable Exposure
$250,000

If AUD weakens 5%
your cost could increase by

$18,700
Trigger conditions:
Copy code

impact_5pct > user_risk_threshold
2. Settlement Window Alerts
These alerts activate when large exposures approach settlement.
Example:
Copy code

Your USD payment of 180,000
is due in 21 days.

Recent FX volatility suggests
a potential impact of $12,400.
Trigger conditions:
Copy code

days_to_due < settlement_alert_window
AND
exposure > threshold
Example threshold:
Copy code

50,000 foreign currency
3. Psychological Level Alerts
SMEs frequently respond to key FX levels.
Example levels:
Copy code

AUDUSD
0.70
0.72
0.75

AUDGBP
0.55
These levels often trigger increased trading activity.
Example alert:
Copy code

AUD/USD has reached 0.70.

Many businesses secure FX rates at this level.
You may wish to review your USD exposure.
Trigger logic:
Copy code

spot_rate crosses psychological_level
4. Favourable Market Alerts
These alerts notify users when the market moves in their favour.
Example:
Copy code

AUD/USD has improved from 0.66 to 0.69.

If you were considering hedging,
this may be a favourable opportunity.
These alerts are powerful because they reinforce:
Copy code

regret avoidance
Many SMEs regret missing favourable FX levels.
5. Adverse Movement Alerts
These alerts trigger when the market moves against the user.
Example:
Copy code

AUD has weakened 3% this week.

Your USD payable exposure
is now $9,800 more expensive.
This provides early awareness before settlement.
6. Macro Event Alerts
Major economic releases can significantly move FX markets.
Examples:
Copy code

FOMC interest rate decisions
US CPI inflation
Nonfarm payrolls
RBA meetings
Example alert:
Copy code

US CPI data is released tonight.

This event often moves AUD/USD significantly.
These alerts should only appear when the business has exposure in affected currencies.
7. Exposure Growth Alerts
These alerts trigger when the system detects growing exposure.
Example:
Copy code

Your USD exposure has increased
from $120,000 to $310,000 this month.
This often occurs when businesses grow quickly.
8. Recurring Pattern Alerts
If the system detects regular FX payments, it should inform the user.
Example:
Copy code

You typically pay USD suppliers monthly.

Average exposure
$85,000
This insight helps businesses plan hedging strategies earlier.
9. Risk Reduction Feedback
Positive reinforcement improves long-term engagement.
Example:
Copy code

Good decision.

Your hedge reduced FX risk by
$9,400.
This message appears after exposure is reduced.
Alert Frequency Control
To avoid overwhelming users, alerts should be limited.
Recommended rules:
Copy code

Maximum 1 major alert per day
Maximum 3 alerts per week
High urgency alerts may override limits.
Alert Delivery Channels
Alerts should eventually support multiple delivery methods.
Examples:
Copy code

email
dashboard notifications
mobile push
Slack
Early versions can start with dashboard notifications.
Personalisation
Users should be able to configure preferences.
Example settings:
Copy code

alert threshold
currencies monitored
macro event alerts
settlement alerts
Alert Severity Levels
Each alert should have a severity rating.
Example:
Copy code

LOW
MEDIUM
HIGH
URGENT
This helps prioritise attention.
Example Alert Flow
Example scenario:
Copy code

Business has USD payable
$200,000

Settlement
45 days
System monitoring detects:
Copy code

AUD/USD drops 3%
System calculates:
Copy code

cost increase
$9,000
Alert generated:
Copy code

AUD has weakened 3%.

Your USD exposure could now cost
$9,000 more.

You may wish to review your hedge options.
Long Term Vision
The alert engine should eventually behave like an automated FX advisor.
Instead of reacting to events manually, the system continuously asks:
Copy code

Is the business exposed?
Has the risk changed?
Should the user consider acting?
Strategic Importance
The Alert Engine is one of the most important parts of FX Risk Radar.
Most FX platforms show information.
Very few platforms actively monitor risk and notify users before problems occur.
This feature transforms the product from:
Copy code

FX calculator
into
Copy code

FX risk monitoring platform
Implementation Guidance for Codex
When implementing alert logic, reference:
Copy code

docs/SME_FX_BEHAVIOUR.md
docs/HEDGING_LOGIC.md
docs/SYSTEM_ARCHITECTURE.md
docs/ALERT_LOGIC.md
These documents define the product's decision framework.
One Very Interesting Thing From Research
Your dealer experience uncovered something that research confirms:
SMEs do not need more market data.
They need:
Copy code

timely warnings
simple explanations
clear action suggestions
That exact combination is what FX Risk Radar is designed to deliver.
