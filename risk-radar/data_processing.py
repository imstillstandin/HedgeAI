from datetime import date

import pandas as pd

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
    return (
        df.groupby(["currency", "type"], as_index=False)
        .agg(
            total_amount=("amount", "sum"),
            avg_rate=("rate", "mean"),
            nearest_due_date=("due_date", "min"),
            line_count=("amount", "count"),
        )
        .sort_values(["currency", "type"])
    )


def add_scenarios(summary: pd.DataFrame, scenario_fn, hedge_fn, health_fn) -> pd.DataFrame:
    rows = []
    today = date.today()

    for _, row in summary.iterrows():
        scenarios = scenario_fn(amount=row["total_amount"], rate=row["avg_rate"])
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
        lambda r: hedge_fn(amount=r["total_amount"], days_to_due=r["days_to_due"], exposure_type=r["type"]), axis=1
    )
    result["fx_health_score"] = result.apply(health_fn, axis=1)
    return result.sort_values(["currency", "type"])
