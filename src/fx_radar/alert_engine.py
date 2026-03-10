"""Alert generation logic for high-signal FX risk notifications."""

from __future__ import annotations

import pandas as pd


def generate_alerts(
    scenario_df: pd.DataFrame,
    impact_threshold_aud: float = 3000,
    settlement_window_days: int = 30,
    settlement_amount_threshold: float = 50000,
) -> pd.DataFrame:
    """Generate deterministic dashboard alerts from scenario rows.

    The rule set focuses on signal over noise:
    - risk threshold alerts when 5% impact exceeds AUD threshold
    - settlement alerts for large exposures due soon
    """
    if scenario_df.empty:
        return pd.DataFrame(columns=["severity", "category", "currency", "type", "message", "action"])

    alerts: list[dict[str, str]] = []

    for _, row in scenario_df.iterrows():
        impact = abs(float(row["impact_5pct"]))
        amount = float(row["total_amount"])
        days_to_due = int(row["days_to_due"])

        if impact >= impact_threshold_aud:
            severity = "HIGH" if impact >= impact_threshold_aud * 2 else "MEDIUM"
            alerts.append(
                {
                    "severity": severity,
                    "category": "risk_threshold",
                    "currency": str(row["currency"]),
                    "type": str(row["type"]),
                    "message": (
                        f"A 5% AUD move could impact {row['currency']} {row['type']} by about "
                        f"${impact:,.0f}."
                    ),
                    "action": "Review hedge coverage for this exposure.",
                }
            )

        if days_to_due <= settlement_window_days and amount >= settlement_amount_threshold:
            severity = "URGENT" if days_to_due <= 14 else "HIGH"
            alerts.append(
                {
                    "severity": severity,
                    "category": "settlement_window",
                    "currency": str(row["currency"]),
                    "type": str(row["type"]),
                    "message": (
                        f"{row['currency']} {row['type']} exposure of {amount:,.0f} is due in "
                        f"{days_to_due} days."
                    ),
                    "action": "Confirm settlement plan and hedge decision timeline.",
                }
            )

    result = pd.DataFrame(alerts)
    if result.empty:
        return pd.DataFrame(columns=["severity", "category", "currency", "type", "message", "action"])

    severity_order = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    return result.sort_values(by="severity", key=lambda s: s.map(severity_order)).reset_index(drop=True)
