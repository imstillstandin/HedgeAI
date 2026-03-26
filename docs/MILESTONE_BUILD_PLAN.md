# FX Risk Radar — Milestone Build Plan

## Purpose
This plan translates the product strategy and system architecture into practical delivery milestones for a clean, simple, and beautiful SME-focused FX hedging tool.

It is intentionally aligned with:
- `Docs/PRODUCT_STRATEGY.md`
- `Docs/SYSTEM_ARCHITECTURE.md`
- `Docs/AGENT_CONTEXT.md`
- `Docs/SME_FX_BEHAVIOUR.md`
- `Docs/HEDGING_LOGIC`
- `Docs/ALERT_LOGIC`

---

## North Star
Build the "digital FX risk manager" for SME owners by keeping outputs simple, actionable, and tied to business impact (profit, margin, and cash-flow risk), not market jargon.

Success principles:
1. Separate business logic from UI logic.
2. Prioritise decision support over prediction.
3. Provide clear next actions for each risk insight.
4. Keep alert quality high (signal over noise).

---

## Milestone 1 — Foundation Refactor (Weeks 1–2)
### Goal
Move from single-file prototype to modular architecture without changing user-facing outcomes.

### Scope
1. **Create modular package structure**
   - `src/fx_radar/ingestion.py`
   - `src/fx_radar/exposure_engine.py`
   - `src/fx_radar/risk_engine.py`
   - `src/fx_radar/alert_engine.py` (initial scaffolding)
   - `src/fx_radar/presentation.py`
   - `src/fx_radar/models.py` (typed data objects)
2. **Refactor existing logic out of `app.py`**
   - Validation/normalization into ingestion layer.
   - Exposure aggregation into exposure engine.
   - Scenario and hedge logic into risk engine.
   - Formatting and human-readable messaging into presentation layer.
3. **Define canonical exposure schema**
   - Standard fields: `currency`, `amount`, `type`, `due_date`, `rate`, plus metadata placeholders (`source_system`, `source_id`, `status`).
4. **Unit-test core engines**
   - Validation edge cases.
   - Scenario math consistency.
   - Hedge suggestion thresholds.
   - Health score bounds and monotonic behaviour.

### Deliverables
- Modular codebase with unchanged functional behavior in UI.
- Baseline unit test suite for ingestion/exposure/risk modules.
- `app.py` reduced to orchestration + rendering.

### Exit Criteria
- No business logic remains embedded directly in Streamlit event blocks.
- Existing CSV + manual workflows still run end-to-end.
- Tests pass in CI/local.

---

## Milestone 2 — Risk Intelligence v1 (Weeks 3–5)
### Goal
Improve decision quality and trust by making recommendations configurable and explainable.

### Scope
1. **Configurable hedge policy profiles**
   - Add `config/hedge_profiles.yaml` with `conservative`, `balanced`, `growth`.
   - Replace hardcoded hedge ranges with policy-driven rules.
2. **Enhance risk engine outputs**
   - Add 3%, 5%, and 10% scenarios.
   - Add concentration risk indicators.
   - Add simple "cost of inaction" estimate based on settlement windows.
3. **Assumptions + confidence layer**
   - Display scenario assumptions and data quality flags.
   - Add confidence ratings (high/medium/low) based on data completeness + timing.
4. **UX copy quality pass**
   - Rewrite summaries to be plain-English and action-oriented.
   - Avoid technical FX jargon where possible.

### Deliverables
- Policy-driven recommendation engine.
- Explainable risk output blocks with assumptions and confidence.
- Improved risk summary cards and narrative insights.

### Exit Criteria
- Recommendation logic can be changed by config (no code edits required).
- Every recommendation has explanation text.
- At least one clear next-step shown per major risk insight.

---

## Milestone 3 — Alert Engine MVP (Weeks 6–8)
### Goal
Evolve from static dashboard to monitoring assistant.

### Scope
1. **Rule-based alert engine implementation**
   - Risk-threshold alerts.
   - Settlement-window alerts.
   - Concentration alerts.
   - Psychological level alert structure (data feed integration placeholder if needed).
2. **Alert quality controls**
   - Severity levels (LOW/MEDIUM/HIGH/URGENT).
   - Frequency caps (e.g., daily/weekly limits).
   - Currency relevance filters (alert only on active exposure currencies).
3. **In-app alert center UI**
   - "Triggered now" panel.
   - "Why this alert" explanation.
   - "Suggested action" text.
   - Dismiss/snooze state for prototype.

### Deliverables
- Functional alert engine producing deterministic results from current exposure data.
- Streamlit alert center with severity and action guidance.

### Exit Criteria
- Alerts are sparse but meaningful (signal-first behavior).
- Alerts map clearly to either financial impact or timing urgency.

---

## Milestone 4 — SME Workflow & Design Polish (Weeks 9–10)
### Goal
Deliver a cleaner, more beautiful user experience aligned to SME mental models.

### Scope
1. **UX simplification and layout improvements**
   - Clear top-level flow: Exposure → Risk → Action.
   - Reduce table overload with progressive disclosure.
   - Highlight one "Top priority" decision per session.
2. **Visual consistency pass**
   - Unified spacing, typography hierarchy, status colours.
   - Card-based risk summaries for quick scanning.
3. **Action workflows**
   - "Prepare broker conversation" summary export.
   - Hedge plan summary (partial hedge options, timing guidance).
4. **Trust layer**
   - Clarify guidance vs advice boundaries.
   - Show timestamp/source context for all key numbers.

### Deliverables
- Cleaner dashboard with clear visual hierarchy.
- Decision-focused workflows and exportable summaries.

### Exit Criteria
- A first-time SME user can answer in under 2 minutes:
  1) What is my biggest FX risk?
  2) What action should I consider now?

---

## Milestone 5 — Production Readiness Baseline (Weeks 11–12)
### Goal
Prepare for broader pilot usage and reliable iteration.

### Scope
1. **Quality and reliability**
   - Add integration tests for upload/manual/combined flows.
   - Add regression tests for risk math and alert triggering.
2. **Observability and diagnostics**
   - Structured logging around ingestion, risk calculations, and alert decisions.
   - Error telemetry hooks for failed uploads and invalid data.
3. **Data and settings persistence**
   - Introduce lightweight persistence layer for user settings and alert preferences.
4. **Deployment hygiene**
   - Environment-based config.
   - Basic release checklist and rollback notes.

### Deliverables
- Stable pilot-ready baseline.
- Documented runbooks for common data and logic issues.

### Exit Criteria
- Core workflows are test-covered and reproducible.
- Critical failures are observable and diagnosable.

---

## Backlog (Post-Milestone 5)
- Accounting system integrations (Xero/QuickBooks/MYOB).
- Broker connectivity and execution handoff workflows.
- Historical exposure analytics and recurring-pattern detection.
- Multi-channel alert delivery (email/push/Slack).
- Benchmarking and optimisation tooling for hedge policy tuning.

---

## KPI Framework by Milestone
1. **Usability KPI**: Time-to-first-insight (target < 2 minutes).
2. **Decision KPI**: Percentage of users who take an action after risk review.
3. **Trust KPI**: Reduction in "unclear output" feedback.
4. **Engagement KPI**: Weekly return sessions after alert MVP.
5. **Risk KPI**: Reduction in unmonitored near-term high-impact exposures.

---

## Build Order Rationale
- Milestone 1 creates the architecture needed for safe, rapid iteration.
- Milestone 2 upgrades the product moat (domain-led risk guidance).
- Milestone 3 introduces proactive value via monitoring.
- Milestone 4 improves adoption through cleaner UX and actionability.
- Milestone 5 ensures reliability before scale.

This sequence protects product quality while moving quickly toward a differentiated SME treasury decision platform.
