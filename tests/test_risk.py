import unittest

from hedgeai.risk import calculate_health_score, scenario_analysis, suggest_hedge_range


class RiskLogicTests(unittest.TestCase):
    def test_scenario_analysis_outputs_expected_keys(self):
        result = scenario_analysis(amount=100000, rate=0.66)
        self.assertEqual(
            set(result.keys()),
            {
                "current_aud_value",
                "aud_value_if_aud_weakens_5pct",
                "aud_value_if_aud_weakens_10pct",
                "impact_5pct",
                "impact_10pct",
            },
        )
        self.assertGreater(result["impact_5pct"], 0)

    def test_suggest_hedge_range_for_large_near_term_payable(self):
        self.assertEqual(suggest_hedge_range(150000, 30, "payable"), "40% to 60%")

    def test_suggest_hedge_range_for_small_receivable(self):
        self.assertEqual(suggest_hedge_range(20000, 120, "receivable"), "Monitor or low hedge need")

    def test_calculate_health_score_reduces_for_high_impact_and_short_tenor(self):
        row = {"impact_5pct": 25000, "days_to_due": 20, "type": "payable"}
        score = calculate_health_score(row)
        self.assertEqual(score, 50)


if __name__ == "__main__":
    unittest.main()
