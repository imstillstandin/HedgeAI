"""Display-focused formatting helpers for Streamlit UI."""

from __future__ import annotations

import pandas as pd

from .models import HedgeDecision


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
        f"- Reference/booked exposure rates are distinct from live market spot rates.  \n"
        f"- Risk analysis: A 5% weakening in AUD could {effect_text} by about **{format_currency(abs(row['impact_5pct']))}**  \n"
        f"- Risk urgency: **{row['urgency_level'].upper()}** — {row['urgency_message']}  \n"
        f"- FX Health Score: **{row['fx_health_score']}/100**"
    )


def format_reason_codes(reason_codes: list[str]) -> list[str]:
    """Convert machine reason codes into human-readable labels."""
    return [code.replace("_", " ").title() for code in reason_codes]


def format_execution_mode(execution_mode: str) -> str:
    """Format decision execution mode label for display."""
    return execution_mode.replace("_", " ").title()


def format_instrument_label(instrument: str) -> str:
    """Format instrument type for display."""
    return instrument.replace("_", " ").title()


def build_decision_summary(decision: HedgeDecision) -> str:
    """Build a concise summary string for one hedge decision."""
    ratio = f"{decision.final_hedge_ratio:.0%}"
    return (
        f"{decision.exposure_id}: {decision.exposure_type.title()} {decision.currency} | "
        f"Hedge {ratio} | {format_instrument_label(decision.instrument)} | "
        f"{format_execution_mode(decision.execution_mode)}"
    )
