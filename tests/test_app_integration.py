"""Integration-style checks for app wiring with hedge policy engine."""

from __future__ import annotations

import ast
from pathlib import Path
import sys
import types

# Allow importing presentation module in minimal test environments.
sys.modules.setdefault("pandas", types.ModuleType("pandas"))

from fx_radar.presentation import (  # noqa: E402
    build_decision_summary,
    format_execution_mode,
    format_instrument_label,
    format_reason_codes,
    generate_summary_text,
)


def _app_ast() -> ast.Module:
    app_source = Path("app.py").read_text(encoding="utf-8")
    return ast.parse(app_source)


def test_app_imports_and_calls_hedge_policy_engine() -> None:
    module = _app_ast()

    imported = False
    called = False
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom) and node.module == "fx_radar.hedge_policy_engine":
            imported = any(alias.name == "build_portfolio_hedge_decisions" for alias in node.names)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "build_portfolio_hedge_decisions":
            called = True

    assert imported is True
    assert called is True


def test_app_imports_and_uses_market_data_layer() -> None:
    module = _app_ast()

    imported = False
    called = False
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom) and node.module == "fx_radar.market_data":
            imported = any(alias.name == "get_market_context" for alias in node.names)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "get_market_context":
            called = True

    assert imported is True
    assert called is True


def test_app_imports_risk_engine_functions_and_does_not_redefine_them() -> None:
    module = _app_ast()
    app_source = Path("app.py").read_text(encoding="utf-8")

    risk_imported = False
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom) and node.module == "fx_radar.risk_engine":
            imported_names = {alias.name for alias in node.names}
            required = {"scenario_analysis", "classify_urgency", "calculate_health_score", "add_scenarios"}
            risk_imported = required.issubset(imported_names)

    assert risk_imported is True
    assert "def scenario_analysis(" not in app_source
    assert "def classify_urgency(" not in app_source
    assert "def calculate_health_score(" not in app_source
    assert "def add_scenarios(" not in app_source


def test_app_uses_presentation_helpers_for_decisions() -> None:
    app_source = Path("app.py").read_text(encoding="utf-8")

    assert "build_decision_summary(decision)" in app_source
    assert "format_instrument_label(decision.instrument)" in app_source
    assert "format_execution_mode(decision.execution_mode)" in app_source
    assert "format_reason_codes(decision.reason_codes)" in app_source
    assert "def render_hedge_decisions(decisions: list[HedgeDecision])" in app_source
    assert 'st.subheader("8. Deterministic Hedge Policy Decisions")' in app_source


def test_legacy_scenario_and_risk_outputs_still_exist() -> None:
    app_source = Path("app.py").read_text(encoding="utf-8")

    assert "scenario_df = add_scenarios(summary)" in app_source
    assert 'st.subheader("5. Risk Scenarios")' in app_source
    assert 'st.subheader("7. Plain-English Risk Summary")' in app_source
    assert 'st.subheader("6. FX Health Check")' in app_source


def test_presentation_helpers_format_decision_fields() -> None:
    class _Decision:
        exposure_id = "EXP-1"
        exposure_type = "payable"
        currency = "USD"
        final_hedge_ratio = 0.9
        instrument = "layered_forward"
        execution_mode = "auto_execute"

    assert format_reason_codes(["margin_protection"]) == ["Margin Protection"]
    assert format_execution_mode("auto_execute") == "Auto Execute"
    assert format_instrument_label("option_or_participating_forward") == "Option Or Participating Forward"
    assert "EXP-1" in build_decision_summary(_Decision())


def test_legacy_hedge_range_not_primary_recommendation_text() -> None:
    app_source = Path("app.py").read_text(encoding="utf-8")

    assert "practical hedge suggestion" not in app_source
    assert "suggests a simple hedge range based on size and timing" not in app_source
    assert "deterministic hedge policy decisions" in app_source
    assert "suggest_hedge_range(" not in app_source
    assert "suggested_hedge_range" not in app_source
    assert "Manual spot rate" in app_source
    assert "Manual market-context override (advanced)" in app_source
    assert "Reference / booked rate" in app_source
    assert "Current Market Spot Rate" in app_source
    assert "booked/reference rate" in app_source


def test_presentation_risk_summary_excludes_hedge_band_recommendations() -> None:
    row = {
        "currency": "USD",
        "type": "payable",
        "total_amount": 100000.0,
        "days_to_due": 30,
        "impact_5pct": 2500.0,
        "urgency_level": "medium",
        "urgency_message": "Monitor closely.",
        "fx_health_score": 78,
        "suggested_hedge_range": "40% to 60%",
    }
    summary = generate_summary_text(row)
    assert "Suggested hedge range" not in summary
    assert "Risk analysis:" in summary
