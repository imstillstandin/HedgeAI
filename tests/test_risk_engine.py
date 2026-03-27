"""Tests for risk_engine separation from hedge policy decisions."""

from __future__ import annotations

import ast
from pathlib import Path
import sys
import types
import warnings

# Allow importing fx_radar modules in minimal test environments.
sys.modules.setdefault("pandas", types.ModuleType("pandas"))

from fx_radar.risk_engine import calculate_health_score, scenario_analysis, suggest_hedge_range


def test_scenario_analysis_and_health_score_still_work() -> None:
    scenario = scenario_analysis(amount=100_000, rate=0.66)
    assert set(scenario.keys()) == {
        "current_aud_value",
        "aud_value_if_aud_weakens_5pct",
        "aud_value_if_aud_weakens_10pct",
        "impact_5pct",
        "impact_10pct",
    }

    score = calculate_health_score({"impact_5pct": 25_000, "days_to_due": 20, "type": "payable"})
    assert score == 50


def test_add_scenarios_is_risk_only_without_hedge_band_column() -> None:
    source = Path("src/fx_radar/risk_engine.py").read_text(encoding="utf-8")
    module = ast.parse(source)

    add_scenarios_node = next(
        node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "add_scenarios"
    )
    add_scenarios_source = ast.get_source_segment(source, add_scenarios_node) or ""

    assert "urgency_level" in add_scenarios_source
    assert "fx_health_score" in add_scenarios_source
    assert "suggested_hedge_range" not in add_scenarios_source


def test_suggest_hedge_range_is_deprecated() -> None:
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        message = suggest_hedge_range(150_000, 30, "payable")

    assert message == "Deprecated: use deterministic hedge policy engine."
    assert any(record.category is DeprecationWarning for record in records)
