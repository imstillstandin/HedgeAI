import streamlit as st
import pandas as pd
from datetime import date

from fx_radar.hedge_policy_engine import build_portfolio_hedge_decisions
from fx_radar.models import BusinessProfile, ExposureRecord, HedgeDecision, MarketContext
from fx_radar.market_data import MarketDataError, get_market_context
from fx_radar.presentation import (
    build_decision_summary,
    format_execution_mode,
    format_instrument_label,
    format_reason_codes,
    generate_summary_text,
)
from fx_radar.risk_engine import add_scenarios

st.set_page_config(page_title="FX Risk Radar", layout="wide")

REQUIRED_COLUMNS = {"currency", "amount", "type", "due_date", "rate"}


def validate_dataframe(df: pd.DataFrame):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return False, f"Missing columns: {', '.join(sorted(missing))}"
    return True, "OK"


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]

    valid, message = validate_dataframe(df)
    if not valid:
        raise ValueError(message)

    df["currency"] = df["currency"].astype(str).str.upper().str.strip()
    df["amount"] = pd.to_numeric(df["amount"], errors="raise")
    df["rate"] = pd.to_numeric(df["rate"], errors="raise")
    df["type"] = df["type"].astype(str).str.lower().str.strip()
    df["due_date"] = pd.to_datetime(df["due_date"], errors="raise").dt.date

    if not df["type"].isin(["payable", "receivable"]).all():
        invalid_types = df.loc[~df["type"].isin(["payable", "receivable"]), "type"].unique()
        raise ValueError(
            f"type column must contain only 'payable' or 'receivable'. Found: {', '.join(map(str, invalid_types))}"
        )

    if (df["amount"] <= 0).any():
        raise ValueError("All amounts must be greater than zero.")

    if (df["rate"] <= 0).any():
        raise ValueError("All rates must be greater than zero.")

    return df


def aggregate_exposures(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["currency", "type"], as_index=False)
        .agg(
            total_amount=("amount", "sum"),
            avg_rate=("rate", "mean"),
            nearest_due_date=("due_date", "min"),
            line_count=("amount", "count"),
        )
        .sort_values(["currency", "type"])
    )
    return grouped


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def build_demo_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"currency": "USD", "amount": 180000, "type": "payable", "due_date": "2026-04-20", "rate": 0.66},
            {"currency": "USD", "amount": 95000, "type": "payable", "due_date": "2026-05-18", "rate": 0.66},
            {"currency": "EUR", "amount": 70000, "type": "receivable", "due_date": "2026-04-28", "rate": 0.61},
            {"currency": "GBP", "amount": 30000, "type": "payable", "due_date": "2026-05-05", "rate": 0.49},
        ]
    )


def build_business_profile() -> BusinessProfile:
    """Build business profile from sidebar controls."""
    with st.sidebar:
        st.header("Hedge Policy Inputs")
        annual_revenue = st.number_input(
            "Annual revenue (home currency)",
            min_value=100_000.0,
            value=5_000_000.0,
            step=100_000.0,
        )
        gross_margin_pct = st.number_input("Gross margin %", min_value=0.0, max_value=100.0, value=30.0, step=0.5)
        minimum_margin_pct = st.number_input(
            "Minimum margin %",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=0.5,
        )
        risk_mode = st.selectbox("Risk mode", ["protect_margin", "balanced", "opportunistic"])
        allow_options = st.checkbox("Allow options", value=False)
        natural_hedge_enabled = st.checkbox("Enable natural hedge offsets", value=True)
        budget_rate_enabled = st.checkbox("Enable target budget rate", value=False)
        target_budget_rate = st.number_input(
            "Target budget rate",
            min_value=0.0001,
            value=0.66,
            step=0.0001,
            format="%.4f",
            disabled=not budget_rate_enabled,
        )
        worst_case_rate_enabled = st.checkbox("Enable worst-case margin trigger", value=False)
        worst_case_rate = st.number_input(
            "Worst-case rate",
            min_value=0.0001,
            value=0.60,
            step=0.0001,
            format="%.4f",
            disabled=not worst_case_rate_enabled,
        )

    return BusinessProfile(
        home_currency="AUD",
        industry_template="generic_sme",
        risk_mode=risk_mode,
        annual_revenue_home_ccy=annual_revenue,
        gross_margin_pct=gross_margin_pct,
        minimum_margin_pct=minimum_margin_pct,
        allow_options=allow_options,
        natural_hedge_enabled=natural_hedge_enabled,
        target_budget_rate_enabled=budget_rate_enabled,
        target_budget_rate=target_budget_rate if budget_rate_enabled else None,
        worst_case_rate_enabled=worst_case_rate_enabled,
        worst_case_rate=worst_case_rate if worst_case_rate_enabled else None,
    )


def build_market_context() -> MarketContext:
    """Build market context using live market data by default with optional override."""
    with st.sidebar:
        st.header("Market Data")
        pair = st.selectbox(
            "FX pair",
            ["AUD/USD", "AUD/EUR", "AUD/GBP", "AUD/NZD", "AUD/JPY", "AUD/CAD"],
            index=0,
        )
        provider_name = st.selectbox("Market data provider", ["frankfurter"], index=0)
        manual_override = st.checkbox("Manual market-context override (advanced)", value=False)

    live_context: MarketContext | None = None
    market_data_error: str | None = None

    if not manual_override:
        try:
            live_context = get_market_context(pair=pair, provider_name=provider_name)
        except (MarketDataError, ValueError) as exc:
            market_data_error = str(exc)

    if live_context is not None and not manual_override:
        return live_context

    with st.sidebar:
        if market_data_error:
            st.warning(f"Live market data unavailable. Using manual override inputs. {market_data_error}")

        pair_value = st.text_input("Manual pair", value=pair)
        spot_rate = st.number_input("Manual spot rate", min_value=0.0001, value=0.66, step=0.0001, format="%.4f")
        vol_30d = st.number_input("Manual 30-day volatility %", min_value=0.0, value=8.0, step=0.1)
        vol_90d = st.number_input("Manual 90-day volatility %", min_value=0.0, value=9.0, step=0.1)
        chg_30d = st.number_input("Manual pair change 30d %", value=0.0, step=0.1)
        chg_90d = st.number_input("Manual pair change 90d %", value=0.0, step=0.1)

    return MarketContext(
        pair=pair_value,
        spot_rate=spot_rate,
        volatility_30d_pct=vol_30d,
        volatility_90d_pct=vol_90d,
        pair_change_30d_pct=chg_30d,
        pair_change_90d_pct=chg_90d,
        forward_points={30: 0.0, 90: 0.0, 180: 0.0, 365: 0.0},
    )


def build_exposure_records(df: pd.DataFrame) -> list[ExposureRecord]:
    """Map validated dataframe rows to hedge policy exposure records."""
    records: list[ExposureRecord] = []
    for idx, row in df.reset_index(drop=True).iterrows():
        source_type = str(row.get("source_type") or "budget_forecast")
        confidence = float(row.get("confidence") or 0.60)
        linked_revenue = row.get("linked_revenue_home_ccy")
        linked_revenue_home_ccy = None if pd.isna(linked_revenue) else float(linked_revenue)
        natural_offset = row.get("natural_offset_foreign", 0.0)

        records.append(
            ExposureRecord(
                exposure_id=f"EXP-{idx + 1}",
                currency=row["currency"],
                amount=float(row["amount"]),
                exposure_type=row["type"],
                due_date=row["due_date"],
                rate=float(row["rate"]),
                source_type=source_type,
                confidence=confidence,
                linked_revenue_home_ccy=linked_revenue_home_ccy,
                natural_offset_foreign=0.0 if pd.isna(natural_offset) else float(natural_offset),
                source_system=row.get("source_system"),
                source_id=row.get("source_id"),
                status=str(row.get("status") or "open"),
            )
        )
    return records


def render_hedge_decisions(decisions: list[HedgeDecision]) -> None:
    """Render hedge policy decision output in a dedicated section."""
    st.subheader("8. Deterministic Hedge Policy Decisions")
    if not decisions:
        st.info("No hedge policy decisions available.")
        return

    for decision in decisions:
        st.markdown(f"**{build_decision_summary(decision)}**")
        st.write(
            {
                "exposure_id": decision.exposure_id,
                "currency": decision.currency,
                "exposure_type": decision.exposure_type,
                "final_hedge_ratio": decision.final_hedge_ratio,
                "hedge_amount_foreign": decision.hedge_amount_foreign,
                "instrument": format_instrument_label(decision.instrument),
                "execution_mode": format_execution_mode(decision.execution_mode),
                "reason_codes": format_reason_codes(decision.reason_codes),
                "summary_text": decision.summary_text,
            }
        )
        if decision.tranches:
            tranche_df = pd.DataFrame(decision.tranches)
            st.dataframe(tranche_df, use_container_width=True)
        else:
            st.caption("No tranches scheduled.")
        st.markdown("---")


st.title("FX Risk Radar")
st.caption(
    "Analyze FX risk exposures with live market context and review deterministic hedge policy decisions."
)

with st.sidebar:
    st.header("Manual Exposure Entry")

    manual_currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "NZD", "SGD", "JPY", "CAD"])
    manual_amount = st.number_input("Amount", min_value=0.0, value=150000.0, step=1000.0)
    manual_type = st.selectbox("Type", ["payable", "receivable"])
    manual_due_date = st.date_input("Due date")
    manual_rate = st.number_input(
        "Reference / booked rate",
        min_value=0.0001,
        value=0.66,
        step=0.0001,
        format="%.4f",
        help="Transaction-level booked/reference rate for this exposure (not live market spot).",
    )

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
st.caption(
    "In uploaded/manual exposure data, the `rate` field is the exposure's "
    "booked/reference rate. Live market spot is fetched separately in Market Data."
)

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
validated_display = df.rename(columns={"rate": "reference_rate"})
st.dataframe(validated_display, use_container_width=True)

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
display_summary = display_summary.rename(columns={"avg_rate": "avg_reference_rate"})
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
scenario_display["urgency_level"] = scenario_display["urgency_level"].str.upper()
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
            "urgency_level",
            "urgency_message",
            "fx_health_score",
        ]
    ],
    use_container_width=True,
)

st.subheader("6. FX Health Check")
health_display = scenario_df[
    ["currency", "type", "fx_health_score", "impact_5pct", "urgency_level"]
].copy()
health_display["impact_5pct"] = health_display["impact_5pct"].map(lambda x: format_currency(abs(x)))
health_display["urgency_level"] = health_display["urgency_level"].str.upper()
st.dataframe(health_display, use_container_width=True)

st.subheader("7. Plain-English Risk Summary")
for _, row in scenario_df.iterrows():
    st.markdown(generate_summary_text(row))
    st.markdown("---")

business_profile = build_business_profile()
market_context = build_market_context()
st.subheader("Market Context")
mc1, mc2, mc3, mc4, mc5 = st.columns(5)
mc1.metric("Current Market Spot Rate", f"{market_context.spot_rate:.4f}")
mc2.metric("30d Change", f"{market_context.pair_change_30d_pct:.2f}%")
mc3.metric("90d Change", f"{market_context.pair_change_90d_pct:.2f}%")
mc4.metric("30d Vol", f"{market_context.volatility_30d_pct:.2f}%")
mc5.metric("90d Vol", f"{market_context.volatility_90d_pct:.2f}%")

exposure_records = build_exposure_records(df)
hedge_decisions = build_portfolio_hedge_decisions(
    exposures=exposure_records,
    business_profile=business_profile,
    market_context=market_context,
    today=date.today(),
)
render_hedge_decisions(hedge_decisions)

st.subheader("9. What This Means")
st.write(
    "This report separates risk analysis from policy recommendations. "
    "Risk scenarios and health metrics quantify potential FX impact. "
    "Deterministic hedge policy decisions are generated by the hedge policy engine "
    "and are the primary action layer. "
    "Live market context is handled separately from exposure booked/reference rates. "
    "It supports decision-making and does not predict market direction."
)

with st.expander("Sample CSV format"):
    st.caption("The `rate` column below is the exposure booked/reference rate.")
    st.code(
        """currency,amount,type,due_date,rate
USD,150000,payable,2026-04-25,0.66
USD,90000,payable,2026-05-15,0.66
EUR,50000,receivable,2026-04-30,0.61
""",
        language="csv",
    )
