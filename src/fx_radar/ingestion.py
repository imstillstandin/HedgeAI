"""Input validation and normalization for exposures."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {"currency", "amount", "type", "due_date", "rate"}
OPTIONAL_COLUMNS = {"source_system", "source_id", "status"}


def validate_dataframe(df: pd.DataFrame) -> tuple[bool, str]:
    """Validate required exposure columns are present."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return False, f"Missing columns: {', '.join(sorted(missing))}"
    return True, "OK"


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize and validate exposure rows into canonical schema."""
    cleaned = df.copy()
    cleaned.columns = [c.lower().strip() for c in cleaned.columns]

    valid, message = validate_dataframe(cleaned)
    if not valid:
        raise ValueError(message)

    cleaned["currency"] = cleaned["currency"].astype(str).str.upper().str.strip()
    cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="raise")
    cleaned["rate"] = pd.to_numeric(cleaned["rate"], errors="raise")
    cleaned["type"] = cleaned["type"].astype(str).str.lower().str.strip()
    cleaned["due_date"] = pd.to_datetime(cleaned["due_date"], errors="raise").dt.date

    if not cleaned["type"].isin(["payable", "receivable"]).all():
        invalid_types = cleaned.loc[~cleaned["type"].isin(["payable", "receivable"]), "type"].unique()
        raise ValueError(
            f"type column must contain only 'payable' or 'receivable'. Found: {', '.join(map(str, invalid_types))}"
        )

    if (cleaned["amount"] <= 0).any():
        raise ValueError("All amounts must be greater than zero.")

    if (cleaned["rate"] <= 0).any():
        raise ValueError("All rates must be greater than zero.")

    for col in OPTIONAL_COLUMNS:
        if col not in cleaned.columns:
            cleaned[col] = None

    canonical_order = [
        "currency",
        "amount",
        "type",
        "due_date",
        "rate",
        "source_system",
        "source_id",
        "status",
    ]

    return cleaned[canonical_order]
