import streamlit as st
import pandas as pd
from datetime import date

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


def scenario_analysis(amount: float, rate: float):
    current_aud = amount / rate

    rate_5_down = rate * 0.95
    rate_10_down = rate * 0.90

    aud_5_down = amount / rate_5_down
    aud_10_down = amount / rate_10_down

    impact_5 = aud_5_down - current_aud
    impact_10 = aud_10_down - current_aud

    return {
        "current_aud_value": round(current_aud, 2),
        "aud_value_if_aud_weakens_5pct": round(aud_5_down, 2),
        "aud_value_if_aud_weakens_10pct": round(aud_10_down, 2),
        "impact_5pct": round(impact_5, 2),
        "impact_10pct": round(impact_10, 2),
    }


def suggest_hedge_range(amount: float, days_to_due: int, exposure_type: str) -> str:
    if exposure_type == "payable":
        if amount >= 100000 and days_to_due <= 60:
            return "40% to 60%"
        if amount >= 50000 and days_to_due <= 90:
            return "20% to 40%"
        return "Monitor or low hedge need"

    if exposure_type == "receivable":
        if amount >= 100000 and days_to_due <= 60:
            return "30% to 50%"
        if amount >= 50000 and days_to_due <= 90:
            return "15% to 30%"
        return "Monitor or low hedge need"

    return "No suggestion"


def calculate_health_score(row) -> int:
    score = 100
    impact_5 = abs(row["impact_5pct"])

    if impact_5 > 20000:
        score -= 30
    elif impact_5 > 10000:
        score -= 20
    elif impact_5 > 5000:
        score -= 10

    if row["days_to_due"] <= 30:
        score -= 15
    elif row["days_to_due"] <= 60:
        score -= 10

    if row["type"] == "payable":
        score -= 5

    return max(score, 0)


def add_scenarios(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    today = date.today()

    for _, row in summary.iterrows():
        scenarios = scenario_analysis(
            amount=row["total_amount"],
            rate=row["avg_rate"],
        )

        days_to_due = (row["nearest_due_date"] - today).days

        rows.append(
            {
                "currency": row["currency"],
                "type": row["type"],
                "total_amount": row["total_amount"],
                "avg_rate": round(row["avg_rate"], 4),
                "nearest_due_date": row["nearest_due_date"],
                "days_to_due": days_to_due,
                "line_count": row["line_count"],
                **scenarios,
            }
        )

    result = pd.DataFrame(rows)
    result["suggested_hedge_range"] = result.apply(
        lambda r: suggest_hedge_range(
            amount=r["total_amount"],
            days_to_due=r["days_to_due"],
            exposure_type=r["type"],
        ),
        axis=1,
    )
    result["fx_health_score"] = result.apply(calculate_health_score, axis=1)
    return result.sort_values(["currency", "type"])


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def generate_summary_text(row) -> str:
    if row["type"] == "payable":
        effect_text = "increase your AUD cost"
    else:
        effect_text = "increase your AUD value received"

    if row["days_to_due"] < 0:
        due_text = f"{abs(row['days_to_due'])} days overdue/past due"
    elif row["days_to_due"] == 0:
        due_text = "due today"
    else:
        due_text = f"due in {row['days_to_due']} days"

    return (
        f"**{row['currency']} {row['type']} exposure**  \n"
        f"- Total exposure: {row['total_amount']:,.0f} {row['currency']}  \n"
        f"- Timing: {due_text}  \n"
        f"- A 5% weakening in AUD could {effect_text} by about **{format_currency(abs(row['impact_5pct']))}**  \n"
        f"- Suggested hedge range: **{row['suggested_hedge_range']}**  \n"
        f"- FX Health Score: **{row['fx_health_score']}/100**"
    )


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