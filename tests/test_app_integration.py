import unittest
from pathlib import Path

APP_SOURCE = Path("app.py").read_text()
RENDER_HEDGE_DECISIONS_SOURCE = APP_SOURCE[
    APP_SOURCE.index("def render_hedge_decisions") : APP_SOURCE.index("\nwith st.sidebar:")
]


class AppIntegrationTests(unittest.TestCase):
    def test_app_uses_shared_generate_summary_text_helper(self):
        self.assertNotIn("def generate_summary_text", APP_SOURCE)
        self.assertIn("from src.fx_radar.presentation import generate_summary_text", APP_SOURCE)

    def test_final_sections_appear_in_intuitive_order(self):
        market_context = APP_SOURCE.index('st.subheader("Market Context")')
        policy_decisions = APP_SOURCE.index('st.subheader("8. Deterministic Hedge Policy Decisions")')
        what_this_means = APP_SOURCE.index('st.subheader("9. What This Means")')
        sample_csv = APP_SOURCE.index('with st.expander("Sample CSV format")')

        self.assertLess(market_context, policy_decisions)
        self.assertLess(policy_decisions, what_this_means)
        self.assertLess(what_this_means, sample_csv)

    def test_deterministic_hedge_decision_section_exists(self):
        self.assertIn('st.subheader("8. Deterministic Hedge Policy Decisions")', APP_SOURCE)
        self.assertIn("render_hedge_decisions(build_hedge_decisions(scenario_df))", APP_SOURCE)

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

    def test_hedge_decision_renderer_uses_clean_card_metrics(self):
        self.assertIn("with st.container():", RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertIn('st.markdown(f"### {build_decision_summary(decision)}")', RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertIn("st.columns(4)", RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertIn('metric("Hedge Ratio"', RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertIn('metric("Hedge Amount"', RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertIn('metric("Instrument"', RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertIn('metric("Action"', RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertIn('st.caption(f"Reasons:', RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertIn('st.caption(decision["summary_text"])', RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertIn("st.dataframe(tranche_display", RENDER_HEDGE_DECISIONS_SOURCE)

    def test_hedge_decision_renderer_does_not_render_raw_objects(self):
        self.assertNotIn("st.write({", RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertNotIn("st.write(decision", RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertNotIn("st.json(", RENDER_HEDGE_DECISIONS_SOURCE)
        self.assertNotIn("st.code(", RENDER_HEDGE_DECISIONS_SOURCE)


if __name__ == "__main__":
    unittest.main()
