from __future__ import annotations

import pandas as pd
import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fx_radar.exposure_engine import aggregate_exposures
from fx_radar.ingestion import clean_dataframe
from fx_radar.presentation import format_currency, generate_summary_text
from fx_radar.risk_engine import add_scenarios

st.set_page_config(page_title="FX Risk Radar", layout="wide")


def build_demo_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"currency": "USD", "amount": 180000, "type": "payable", "due_date": "2026-04-20", "rate": 0.66},
            {"currency": "USD", "amount": 95000, "type": "payable", "due_date": "2026-05-18", "rate": 0.66},
            {"currency": "EUR", "amount": 70000, "type": "receivable", "due_date": "2026-04-28", "rate": 0.61},
            {"currency": "GBP", "amount": 30000, "type": "payable", "due_date": "2026-05-05", "rate": 0.49},
        ]
    )


st.title("FX Risk Radar")
st.caption("Upload FX exposures, quantify the risk, and get a practical hedge suggestion.")

with st.sidebar:
    st.header("Manual Exposure Entry")

    manual_currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "NZD", "SGD", "JPY", "CAD"])
    manual_amount = st.number_input("Amount", min_value=0.0, value=150000.0, step=1000.0)
    manual_type = st.selectbox("Type", ["payable", "receivable"])
    manual_due_date = st.date_input("Due date")
    manual_rate = st.number_input("Rate (e.g. AUD/USD)", min_value=0.0001, value=0.66, step=0.0001, format="%.4f")

    if st.button("Use Demo Data"):
        st.session_state["manual_df"] = build_demo_data()

    if st.button("Add Manual Exposure"):
        manual_df = pd.DataFrame(
            [
                {
                    "currency": manual_currency,
                    "amount": manual_amount,
                    "type": manual_type,
                    "due_date": manual_due_date,
                    "rate": manual_rate,
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

st.subheader("2. Validated Input Data")
st.dataframe(df, use_container_width=True)

summary = aggregate_exposures(df)
scenario_df = add_scenarios(summary)

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
scenario_display = scenario_df.copy()
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

st.dataframe(
    scenario_display[
        [
            "currency",
            "type",
            "total_amount",
            "avg_rate",
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

st.subheader("6. FX Health Check")
health_display = scenario_df[["currency", "type", "fx_health_score", "impact_5pct", "suggested_hedge_range"]].copy()
health_display["impact_5pct"] = health_display["impact_5pct"].map(lambda x: format_currency(abs(x)))
st.dataframe(health_display, use_container_width=True)

st.subheader("7. Plain-English Risk Summary")
for _, row in scenario_df.iterrows():
    st.markdown(generate_summary_text(row))
    st.markdown("---")

st.subheader("8. What This Means")
st.write(
    "This report identifies your current foreign currency exposures, estimates the impact "
    "of FX market movements, and suggests a simple hedge range based on size and timing. "
    "It is designed to support decision-making, not predict market direction."
)

with st.expander("Sample CSV format"):
    st.code(
        """currency,amount,type,due_date,rate
USD,150000,payable,2026-04-25,0.66
USD,90000,payable,2026-05-15,0.66
EUR,50000,receivable,2026-04-30,0.61
""",
        language="csv",
    )
