from __future__ import annotations

import unittest
from datetime import date, timedelta
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fx_radar.exposure_engine import aggregate_exposures
from fx_radar.ingestion import clean_dataframe, validate_dataframe
from fx_radar.risk_engine import add_scenarios, calculate_health_score, scenario_analysis, suggest_hedge_range


class IngestionTests(unittest.TestCase):
    def test_validate_dataframe_missing_columns(self):
        valid, message = validate_dataframe(pd.DataFrame({"currency": ["USD"]}))
        self.assertFalse(valid)
        self.assertIn("Missing columns", message)

    def test_clean_dataframe_normalizes_and_adds_optional_fields(self):
        raw = pd.DataFrame(
            {
                "Currency": [" usd "],
                "Amount": [100000],
                "Type": ["Payable"],
                "Due_Date": ["2026-01-15"],
                "Rate": [0.66],
            }
        )
        cleaned = clean_dataframe(raw)
        self.assertEqual(cleaned.loc[0, "currency"], "USD")
        self.assertEqual(cleaned.loc[0, "type"], "payable")
        self.assertTrue(pd.isna(cleaned.loc[0, "source_system"]))
        self.assertEqual(
            list(cleaned.columns),
            ["currency", "amount", "type", "due_date", "rate", "source_system", "source_id", "status"],
        )

    def test_clean_dataframe_rejects_bad_type(self):
        raw = pd.DataFrame(
            {
                "currency": ["USD"],
                "amount": [100],
                "type": ["other"],
                "due_date": ["2026-01-01"],
                "rate": [0.66],
            }
        )
        with self.assertRaisesRegex(ValueError, "payable"):
            clean_dataframe(raw)


class ExposureAndRiskTests(unittest.TestCase):
    def test_aggregate_exposures_groups_currency_and_type(self):
        df = pd.DataFrame(
            {
                "currency": ["USD", "USD", "EUR"],
                "amount": [100, 200, 50],
                "type": ["payable", "payable", "receivable"],
                "due_date": [date(2026, 1, 10), date(2026, 1, 5), date(2026, 2, 1)],
                "rate": [0.66, 0.68, 0.61],
            }
        )
        grouped = aggregate_exposures(df)
        usd = grouped[(grouped["currency"] == "USD") & (grouped["type"] == "payable")].iloc[0]
        self.assertEqual(usd["total_amount"], 300)
        self.assertEqual(usd["line_count"], 2)
        self.assertEqual(usd["nearest_due_date"], date(2026, 1, 5))

    def test_scenario_analysis_outputs_increasing_impact(self):
        out = scenario_analysis(amount=100000, rate=0.66)
        self.assertGreater(out["impact_10pct"], out["impact_5pct"])
        self.assertGreater(out["current_aud_value"], 0)

    def test_suggest_hedge_range_thresholds(self):
        self.assertEqual(suggest_hedge_range(120000, 30, "payable"), "40% to 60%")
        self.assertEqual(suggest_hedge_range(60000, 70, "receivable"), "15% to 30%")

    def test_calculate_health_score_bounds(self):
        row = pd.Series({"impact_5pct": 50000, "days_to_due": 5, "type": "payable"})
        score = calculate_health_score(row)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_add_scenarios_includes_core_columns(self):
        summary = pd.DataFrame(
            [
                {
                    "currency": "USD",
                    "type": "payable",
                    "total_amount": 200000,
                    "avg_rate": 0.66,
                    "nearest_due_date": date.today() + timedelta(days=20),
                    "line_count": 1,
                }
            ]
        )
        scen = add_scenarios(summary)
        expected = {"impact_5pct", "impact_10pct", "suggested_hedge_range", "fx_health_score", "days_to_due"}
        self.assertTrue(expected.issubset(set(scen.columns)))


if __name__ == "__main__":
    unittest.main()
