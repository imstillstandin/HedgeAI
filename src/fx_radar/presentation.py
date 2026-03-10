"""Display-focused formatting helpers for Streamlit UI."""

from __future__ import annotations

import pandas as pd


def format_currency(value: float) -> str:
    """Format number as whole-dollar AUD string."""
    return f"${value:,.0f}"


def generate_summary_text(row: pd.Series) -> str:
    """Generate plain-English risk summary for one exposure group."""
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
