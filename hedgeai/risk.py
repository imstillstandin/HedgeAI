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
