import unittest
from datetime import date, timedelta

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - environment-specific fallback
    pd = None

if pd is not None:
    from hedgeai.data_processing import add_scenarios, aggregate_exposures, clean_dataframe, validate_dataframe


@unittest.skipIf(pd is None, "pandas is required for data_processing tests")
class DataProcessingTests(unittest.TestCase):
    def test_validate_dataframe_detects_missing_columns(self):
        df = pd.DataFrame([{"currency": "USD", "amount": 1000}])
        valid, message = validate_dataframe(df)
        self.assertFalse(valid)
        self.assertIn("due_date", message)
        self.assertIn("rate", message)
        self.assertIn("type", message)

    def test_clean_dataframe_normalizes_and_types_values(self):
        df = pd.DataFrame(
            [
                {
                    "Currency": " usd ",
                    "Amount": "1000",
                    "Type": "Payable",
                    "Due_Date": "2026-04-20",
                    "Rate": "0.66",
                }
            ]
        )
        result = clean_dataframe(df)
        self.assertEqual(result.loc[0, "currency"], "USD")
        self.assertEqual(result.loc[0, "type"], "payable")
        self.assertIsInstance(result.loc[0, "due_date"], date)
        self.assertEqual(result.loc[0, "amount"], 1000)

    def test_clean_dataframe_rejects_invalid_type(self):
        df = pd.DataFrame(
            [
                {
                    "currency": "USD",
                    "amount": 1000,
                    "type": "other",
                    "due_date": "2026-04-20",
                    "rate": 0.66,
                }
            ]
        )
        with self.assertRaises(ValueError):
            clean_dataframe(df)

    def test_aggregate_exposures_groups_rows(self):
        df = pd.DataFrame(
            [
                {"currency": "USD", "amount": 1000, "type": "payable", "due_date": date(2026, 4, 20), "rate": 0.66},
                {"currency": "USD", "amount": 2000, "type": "payable", "due_date": date(2026, 4, 18), "rate": 0.68},
            ]
        )
        aggregated = aggregate_exposures(df)
        self.assertEqual(len(aggregated), 1)
        self.assertEqual(aggregated.loc[0, "total_amount"], 3000)
        self.assertEqual(aggregated.loc[0, "nearest_due_date"], date(2026, 4, 18))
        self.assertEqual(aggregated.loc[0, "line_count"], 2)

    def test_add_scenarios_applies_injected_functions(self):
        due = date.today() + timedelta(days=30)
        summary = pd.DataFrame(
            [
                {
                    "currency": "USD",
                    "type": "payable",
                    "total_amount": 5000,
                    "avg_rate": 0.66,
                    "nearest_due_date": due,
                    "line_count": 1,
                }
            ]
        )

        def scenario_fn(amount, rate):
            return {
                "current_aud_value": round(amount / rate, 2),
                "aud_value_if_aud_weakens_5pct": 1.0,
                "aud_value_if_aud_weakens_10pct": 2.0,
                "impact_5pct": 3.0,
                "impact_10pct": 4.0,
            }

        def hedge_fn(amount, days_to_due, exposure_type):
            return f"{exposure_type}:{days_to_due}:{amount}"

        def health_fn(row):
            return 77 if row["type"] == "payable" else 88

        scenario_df = add_scenarios(summary, scenario_fn, hedge_fn, health_fn)
        self.assertEqual(len(scenario_df), 1)
        self.assertEqual(scenario_df.loc[0, "fx_health_score"], 77)
        self.assertEqual(scenario_df.loc[0, "suggested_hedge_range"].split(":")[0], "payable")


if __name__ == "__main__":
    unittest.main()
