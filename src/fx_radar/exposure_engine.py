"""Exposure aggregation logic."""

from __future__ import annotations

import pandas as pd


def aggregate_exposures(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate exposures by currency and type."""
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
