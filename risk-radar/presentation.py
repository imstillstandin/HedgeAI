import pandas as pd


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
