import unittest
from pathlib import Path

APP_SOURCE = Path("app.py").read_text()


class AppIntegrationTests(unittest.TestCase):
    def test_app_uses_shared_generate_summary_text_helper(self):
        self.assertNotIn("def generate_summary_text", APP_SOURCE)
        self.assertIn("from src.fx_radar.presentation import generate_summary_text", APP_SOURCE)

    def test_final_sections_appear_in_intuitive_order(self):
        market_context = APP_SOURCE.index('st.subheader("Market Context")')
        policy_decisions = APP_SOURCE.index('st.subheader("8. Deterministic Hedge Policy Decisions")')
        what_this_means = APP_SOURCE.index('st.subheader("9. What This Means")')

        self.assertLess(market_context, policy_decisions)
        self.assertLess(policy_decisions, what_this_means)

    def test_risk_scenarios_uses_user_facing_reference_rate_label(self):
        risk_scenarios = APP_SOURCE.index('st.subheader("5. Risk Scenarios")')
        download = APP_SOURCE.index('st.download_button(')
        risk_section = APP_SOURCE[risk_scenarios:download]

        self.assertIn('"avg_reference_rate"', risk_section)
        self.assertNotIn('"avg_rate",', risk_section)

    def test_demo_exposures_include_committed_source_defaults(self):
        self.assertIn('demo_df["source_type"] = "invoice"', APP_SOURCE)
        self.assertIn('demo_df["confidence"] = 1.0', APP_SOURCE)
        self.assertIn("source_type,confidence", APP_SOURCE)
        self.assertIn("invoice,1.0", APP_SOURCE)

    def test_manual_exposures_capture_source_type_and_confidence(self):
        self.assertIn('manual_source_type = st.selectbox("Source type", SOURCE_TYPE_OPTIONS, index=0)', APP_SOURCE)
        self.assertIn('manual_confidence = st.slider("Confidence"', APP_SOURCE)
        self.assertIn('"source_type": manual_source_type', APP_SOURCE)
        self.assertIn('"confidence": manual_confidence', APP_SOURCE)

    def test_build_exposure_records_defaults_to_invoice_confidence_one(self):
        self.assertIn('source_type = row.get("source_type", "invoice")', APP_SOURCE)
        self.assertIn('confidence = row.get("confidence", 1.0)', APP_SOURCE)
        self.assertIn('source_type = "invoice"', APP_SOURCE)
        self.assertIn('confidence = 1.0', APP_SOURCE)
        self.assertNotIn('row.get("confidence", 1.0) or 1.0', APP_SOURCE)

    def test_hedge_decision_section_renders_dashboard_cards_not_raw_dicts(self):
        policy_decisions = APP_SOURCE.index('st.subheader("8. Deterministic Hedge Policy Decisions")')
        what_this_means = APP_SOURCE.index('st.subheader("9. What This Means")')
        decision_section = APP_SOURCE[policy_decisions:what_this_means]

        self.assertIn("render_hedge_decisions(build_hedge_decisions(scenario_df))", decision_section)
        self.assertIn("st.container(border=True)", APP_SOURCE)
        self.assertIn('metric("Hedge ratio"', APP_SOURCE)
        self.assertIn('metric("Hedge amount"', APP_SOURCE)
        self.assertIn('metric("Instrument"', APP_SOURCE)
        self.assertIn('metric("Execution mode"', APP_SOURCE)
        self.assertIn('st.markdown("**Reason codes**")', APP_SOURCE)
        self.assertIn('st.markdown("**Summary**")', APP_SOURCE)
        self.assertIn('st.markdown("**Tranche schedule**")', APP_SOURCE)
        self.assertNotIn("st.write(decision", APP_SOURCE)
        self.assertNotIn("st.write({", APP_SOURCE)
        self.assertNotIn("st.json(", APP_SOURCE)


if __name__ == "__main__":
    unittest.main()
