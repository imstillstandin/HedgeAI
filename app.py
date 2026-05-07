import pandas as pd
import streamlit as st

from hedgeai.data_processing import add_scenarios, aggregate_exposures, clean_dataframe
from hedgeai.presentation import build_demo_data, format_currency
from src.fx_radar.presentation import generate_summary_text
from hedgeai.risk import calculate_health_score, scenario_analysis, suggest_hedge_range

st.set_page_config(page_title="FX Risk Radar", layout="wide")

st.title("FX Risk Radar")
st.caption("Upload FX exposures, quantify the risk, and get a practical hedge suggestion.")


SOURCE_TYPE_OPTIONS = [
    "invoice",
    "signed_po",
    "loan_repayment",
    "executed_contract",
    "budget_forecast",
    "subscription_forecast",
    "sales_pipeline_weighted",
    "inventory_plan",
]


def build_app_demo_data() -> pd.DataFrame:
    demo_df = build_demo_data().copy()
    demo_df["source_type"] = "invoice"
    demo_df["confidence"] = 1.0
    return demo_df


def build_exposure_records(exposures_df: pd.DataFrame) -> list[dict]:
    records = []
    for _, row in exposures_df.iterrows():
        source_type = row.get("source_type", "invoice")
        confidence = row.get("confidence", 1.0)

        if pd.isna(source_type) or not source_type:
            source_type = "invoice"
        if pd.isna(confidence):
            confidence = 1.0

        records.append(
            {
                "currency": row["currency"],
                "amount": row["amount"],
                "type": row["type"],
                "due_date": row["due_date"],
                "rate": row["rate"],
                "source_type": source_type,
                "confidence": confidence,
            }
        )
    return records


def _hedge_ratio_from_range(hedge_range: str) -> float:
    if "%" not in hedge_range:
        return 0.0

    percentages = []
    for token in hedge_range.replace("%", "").replace("to", " ").split():
        if token.isdigit():
            percentages.append(float(token) / 100)

    return max(percentages) if percentages else 0.0


def build_hedge_decisions(scenario_df: pd.DataFrame) -> list[dict]:
    decisions = []
    for _, row in scenario_df.iterrows():
        hedge_ratio = _hedge_ratio_from_range(row["suggested_hedge_range"])
        hedge_amount = row["total_amount"] * hedge_ratio
        instrument = "Forward contract" if hedge_ratio else "No hedge instrument"
        execution_mode = "Dealer-assisted" if hedge_ratio else "Monitor only"
        reason_codes = [
            f"{row['currency']} {row['type']}",
            f"{row['days_to_due']} days to due date",
            f"{format_currency(abs(row['impact_5pct']))} 5% scenario impact",
        ]

        if row["fx_health_score"] < 70:
            reason_codes.append("Lower FX health score")
        if hedge_ratio == 0:
            reason_codes.append("Policy outcome: monitor")

        tranche_schedule = []
        if hedge_ratio:
            tranche_schedule.append(
                {
                    "timing": "Now",
                    "amount": hedge_amount,
                    "ratio": hedge_ratio,
                }
            )

        decisions.append(
            {
                "currency": row["currency"],
                "type": row["type"],
                "hedge_ratio": hedge_ratio,
                "hedge_amount": hedge_amount,
                "instrument": instrument,
                "execution_mode": execution_mode,
                "reason_codes": reason_codes,
                "summary_text": generate_summary_text(row),
                "tranche_schedule": tranche_schedule,
            }
        )
    return decisions


def build_decision_summary(decision: dict) -> str:
    return f"{decision['currency']} {decision['type']} — {decision['instrument']}"


def render_hedge_decisions(decisions: list[dict]) -> None:
    for decision in decisions:
        with st.container():
            st.markdown(f"### {build_decision_summary(decision)}")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Hedge Ratio", f"{decision['hedge_ratio']:.0%}")
            col2.metric("Hedge Amount", f"{decision['hedge_amount']:,.0f} {decision['currency']}")
            col3.metric("Instrument", decision["instrument"])
            col4.metric("Action", decision["execution_mode"])

            st.caption(f"Reasons: {', '.join(decision['reason_codes'])}")
            st.caption(decision["summary_text"])

            if decision["tranche_schedule"]:
                tranche_display = pd.DataFrame(decision["tranche_schedule"])
                tranche_display["amount"] = tranche_display["amount"].map(
                    lambda amount: f"{amount:,.0f} {decision['currency']}"
                )
                tranche_display["ratio"] = tranche_display["ratio"].map(lambda value: f"{value:.0%}")
                st.dataframe(tranche_display, use_container_width=True, hide_index=True)

            st.divider()

with st.sidebar:
    st.header("Manual Exposure Entry")

    manual_currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "NZD", "SGD", "JPY", "CAD"])
    manual_amount = st.number_input("Amount", min_value=0.0, value=150000.0, step=1000.0)
    manual_type = st.selectbox("Type", ["payable", "receivable"])
    manual_due_date = st.date_input("Due date")
    manual_rate = st.number_input("Rate (e.g. AUD/USD)", min_value=0.0001, value=0.66, step=0.0001, format="%.4f")
    manual_source_type = st.selectbox("Source type", SOURCE_TYPE_OPTIONS, index=0)
    manual_confidence = st.slider("Confidence", min_value=0.0, max_value=1.0, value=1.0, step=0.05)

    if st.button("Use Demo Data"):
        st.session_state["manual_df"] = build_app_demo_data()

    if st.button("Add Manual Exposure"):
        manual_df = pd.DataFrame(
            [
                {
                    "currency": manual_currency,
                    "amount": manual_amount,
                    "type": manual_type,
                    "due_date": manual_due_date,
                    "rate": manual_rate,
                    "source_type": manual_source_type,
                    "confidence": manual_confidence,
                }
            ]
        )

        existing = st.session_state.get("manual_df", pd.DataFrame())
        st.session_state["manual_df"] = pd.concat([existing, manual_df], ignore_index=True)

    if st.button("Clear Manual Data"):
        st.session_state["manual_df"] = pd.DataFrame()

st.subheader("1. Upload Exposure CSV")
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

raw_df = None

if uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read uploaded CSV: {e}")
        st.stop()

manual_df = st.session_state.get("manual_df", pd.DataFrame())

if raw_df is not None and not manual_df.empty:
    combined_df = pd.concat([raw_df, manual_df], ignore_index=True)
elif raw_df is not None:
    combined_df = raw_df
elif not manual_df.empty:
    combined_df = manual_df
else:
    combined_df = None

if combined_df is None:
    st.info("Upload a CSV or use the manual entry / demo data in the sidebar to begin.")
    st.stop()

try:
    df = clean_dataframe(combined_df)
except Exception as e:
    st.error(f"Data validation error: {e}")
    st.stop()

exposure_records = build_exposure_records(df)

st.subheader("2. Validated Input Data")
st.dataframe(df, use_container_width=True)

summary = aggregate_exposures(df)
scenario_df = add_scenarios(
    summary,
    scenario_fn=scenario_analysis,
    hedge_fn=suggest_hedge_range,
    health_fn=calculate_health_score,
)

st.subheader("3. Key Metrics")
total_payables = scenario_df.loc[scenario_df["type"] == "payable", "current_aud_value"].sum()
total_receivables = scenario_df.loc[scenario_df["type"] == "receivable", "current_aud_value"].sum()
largest_impact = scenario_df["impact_5pct"].abs().max() if not scenario_df.empty else 0
avg_health = scenario_df["fx_health_score"].mean() if not scenario_df.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("AUD Value of Payables", format_currency(total_payables))
col2.metric("AUD Value of Receivables", format_currency(total_receivables))
col3.metric("Largest 5% FX Impact", format_currency(largest_impact))
col4.metric("Average FX Health Score", f"{avg_health:.0f}/100")

if not scenario_df.empty:
    highest_risk = scenario_df.loc[scenario_df["impact_5pct"].abs().idxmax()]
    st.warning(
        f"Highest near-term FX risk: {highest_risk['currency']} {highest_risk['type']} "
        f"with an estimated 5% AUD move impact of {format_currency(abs(highest_risk['impact_5pct']))}."
    )

st.subheader("4. Exposure Summary")
display_summary = summary.copy()
display_summary["total_amount"] = display_summary["total_amount"].map(lambda x: f"{x:,.0f}")
display_summary["avg_rate"] = display_summary["avg_rate"].map(lambda x: f"{x:.4f}")
st.dataframe(display_summary, use_container_width=True)

st.subheader("5. Risk Scenarios")
selected_currencies = st.multiselect(
    "Filter currencies",
    options=sorted(scenario_df["currency"].unique()),
    default=sorted(scenario_df["currency"].unique()),
)

if selected_currencies:
    filtered_scenario_df = scenario_df[scenario_df["currency"].isin(selected_currencies)].copy()
else:
    filtered_scenario_df = scenario_df.copy()

scenario_display = filtered_scenario_df.copy()
for col in [
    "current_aud_value",
    "aud_value_if_aud_weakens_5pct",
    "aud_value_if_aud_weakens_10pct",
    "impact_5pct",
    "impact_10pct",
]:
    scenario_display[col] = scenario_display[col].map(format_currency)

scenario_display["total_amount"] = scenario_display["total_amount"].map(lambda x: f"{x:,.0f}")
scenario_display["avg_rate"] = scenario_display["avg_rate"].map(lambda x: f"{x:.4f}")
scenario_display = scenario_display.rename(columns={"avg_rate": "avg_reference_rate"})

st.dataframe(
    scenario_display[
        [
            "currency",
            "type",
            "total_amount",
            "avg_reference_rate",
            "nearest_due_date",
            "days_to_due",
            "current_aud_value",
            "impact_5pct",
            "impact_10pct",
            "suggested_hedge_range",
            "fx_health_score",
        ]
    ],
    use_container_width=True,
)

scenario_export = filtered_scenario_df.rename(columns={"avg_rate": "avg_reference_rate"})

st.download_button(
    "Download filtered scenario table as CSV",
    data=scenario_export.to_csv(index=False).encode("utf-8"),
    file_name="fx_risk_scenarios.csv",
    mime="text/csv",
)

st.subheader("6. FX Health Check")
health_display = scenario_df[["currency", "type", "fx_health_score", "impact_5pct", "suggested_hedge_range"]].copy()
health_display["impact_5pct"] = health_display["impact_5pct"].map(lambda x: format_currency(abs(x)))
st.dataframe(health_display, use_container_width=True)

st.subheader("Market Context")
st.write(
    "Use these outputs as a business impact view of your current FX exposures. "
    "The scenarios are deterministic policy checks based on uploaded exposure size, "
    "timing, type, and reference rate — not live market forecasts."
)

st.subheader("8. Deterministic Hedge Policy Decisions")
st.caption(f"Policy engine evaluated {len(exposure_records)} normalized exposure records.")
render_hedge_decisions(build_hedge_decisions(scenario_df))

st.subheader("9. What This Means")
st.write(
    "This report identifies your current foreign currency exposures, estimates the impact "
    "of FX market movements, and suggests a simple hedge range based on size and timing. "
    "It is designed to support decision-making, not predict market direction."
)

with st.expander("Sample CSV format"):
    st.code(
        """currency,amount,type,due_date,rate,source_type,confidence
USD,150000,payable,2026-04-25,0.66,invoice,1.0
USD,90000,payable,2026-05-15,0.66,invoice,1.0
EUR,50000,receivable,2026-04-30,0.61,invoice,1.0
""",
        language="csv",
    )
