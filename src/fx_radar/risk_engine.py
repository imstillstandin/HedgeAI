"""FX risk and hedging calculations."""

from __future__ import annotations

from datetime import date

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
    """Provide a simple hedge-range suggestion based on size and timing."""
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
    """Add scenario, hedge suggestion, and health score to grouped exposures."""
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
