"""FX risk analysis and scoring calculations."""

from __future__ import annotations

from datetime import date
import warnings

import pandas as pd


def scenario_analysis(amount: float, rate: float) -> dict[str, float]:
    """Calculate AUD value and 5%/10% downside scenarios."""
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
    """Deprecated: hedge recommendations are owned by ``hedge_policy_engine``."""
    warnings.warn(
        "suggest_hedge_range is deprecated. Use hedge_policy_engine for hedge decisions.",
        DeprecationWarning,
        stacklevel=2,
    )
    _ = (amount, days_to_due, exposure_type)
    return "Deprecated: use deterministic hedge policy engine."


def classify_urgency(days_to_due: int, impact_5pct: float) -> tuple[str, str]:
    """Classify urgency using settlement timing and 5% scenario impact."""
    abs_impact = abs(impact_5pct)

    if days_to_due <= 14 or abs_impact >= 20000:
        return "critical", "Near-due and/or high financial impact — review hedge action now."
    if days_to_due <= 30 or abs_impact >= 10000:
        return "high", "Material near-term risk — consider partial hedging soon."
    if days_to_due <= 60 or abs_impact >= 5000:
        return "medium", "Moderate exposure risk — monitor closely and plan next steps."
    return "low", "Lower immediate risk — continue monitoring."


def calculate_health_score(row: pd.Series) -> int:
    """Calculate a simplified FX health score (0-100)."""
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
    """Add scenario metrics, urgency, and health score to grouped exposures."""
    rows: list[dict] = []
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
    if result.empty:
        return result

    urgency = result.apply(
        lambda r: classify_urgency(
            days_to_due=r["days_to_due"],
            impact_5pct=r["impact_5pct"],
        ),
        axis=1,
    )
    result["urgency_level"] = urgency.map(lambda x: x[0])
    result["urgency_message"] = urgency.map(lambda x: x[1])
    result["fx_health_score"] = result.apply(calculate_health_score, axis=1)
    return result.sort_values(["currency", "type"])
