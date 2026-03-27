"""Tests for the deterministic hedge policy engine."""

from __future__ import annotations

from datetime import date, timedelta
import sys
import types

# Avoid importing optional heavy deps via fx_radar.__init__ during test collection.
sys.modules.setdefault("pandas", types.ModuleType("pandas"))

from fx_radar.hedge_policy_engine import (
    build_hedge_decision,
    build_tranche_schedule,
    calculate_final_hedge_ratio,
    calculate_net_exposure,
    classify_certainty,
    classify_time_bucket,
    determine_execution_mode,
    select_instrument,
)
from fx_radar.models import BusinessProfile, ExposureRecord, HedgeDecision, MarketContext


def _business_profile(**overrides: object) -> BusinessProfile:
    base = {
        "home_currency": "USD",
        "industry_template": "generic",
        "risk_mode": "protect_margin",
        "annual_revenue_home_ccy": 2_000_000.0,
        "gross_margin_pct": 20.0,
        "minimum_margin_pct": 12.0,
    }
    base.update(overrides)
    return BusinessProfile(**base)


def _market_context(**overrides: object) -> MarketContext:
    base = {
        "pair": "USD/EUR",
        "spot_rate": 1.10,
        "volatility_30d_pct": 10.0,
        "volatility_90d_pct": 9.0,
        "pair_change_30d_pct": -4.0,
        "pair_change_90d_pct": -6.0,
        "forward_points": {30: 0.001},
    }
    base.update(overrides)
    return MarketContext(**base)


def _exposure(today: date, **overrides: object) -> ExposureRecord:
    base = {
        "exposure_id": "exp-1",
        "currency": "EUR",
        "amount": 100_000.0,
        "exposure_type": "payable",
        "due_date": today + timedelta(days=45),
        "rate": 1.10,
        "source_type": "budget_forecast",
        "confidence": 0.85,
    }
    base.update(overrides)
    return ExposureRecord(**base)


def test_classify_certainty() -> None:
    assert classify_certainty("invoice", 0.2) == "committed"
    assert classify_certainty("signed_po", 0.1) == "committed"
    assert classify_certainty("budget_forecast", 0.70) == "forecast_high"
    assert classify_certainty("sales_pipeline_weighted", 0.50) == "forecast_medium"
    assert classify_certainty("inventory_plan", 0.20) == "forecast_low"
    assert classify_certainty("unknown_source", 0.95) == "forecast_low"


def test_classify_time_bucket() -> None:
    assert classify_time_bucket(10) == "0_30"
    assert classify_time_bucket(90) == "31_90"
    assert classify_time_bucket(120) == "91_180"
    assert classify_time_bucket(300) == "181_365"
    assert classify_time_bucket(500) == "365_plus"


def test_calculate_net_exposure() -> None:
    assert calculate_net_exposure(100.0, 40.0, True) == 60.0
    assert calculate_net_exposure(100.0, 200.0, True) == 0.0
    assert calculate_net_exposure(100.0, 80.0, False) == 100.0


def test_calculate_final_hedge_ratio() -> None:
    profile = _business_profile(gross_margin_pct=18.0, minimum_margin_pct=13.0)
    market = _market_context(volatility_30d_pct=12.0, pair_change_30d_pct=-4.0, pair_change_90d_pct=-6.0)

    ratio = calculate_final_hedge_ratio(
        certainty_class="forecast_high",
        time_bucket="31_90",
        business_profile=profile,
        market_context=market,
        exposure_type="payable",
    )

    # 0.70 + 0.00 + 0.15 + 0.10 + 0.10 => 1.05 clamped to 0.85
    assert ratio == 0.85


def test_margin_trigger_forces_ratio_floor() -> None:
    today = date(2026, 3, 27)
    profile = _business_profile(
        gross_margin_pct=11.0,
        minimum_margin_pct=10.0,
        worst_case_rate_enabled=True,
        worst_case_rate=0.80,
    )
    market = _market_context(spot_rate=1.10, volatility_30d_pct=20.0)
    exposure = _exposure(
        today,
        source_type="budget_forecast",
        confidence=0.60,
        amount=2_000_000.0,
        rate=0.80,
        due_date=today + timedelta(days=120),
        linked_revenue_home_ccy=2_100_000.0,
        exposure_type="payable",
    )

    decision = build_hedge_decision(exposure, profile, market, today)

    assert decision.margin_triggered is True
    assert decision.final_hedge_ratio >= 0.90


def test_budget_trigger_increases_ratio() -> None:
    today = date(2026, 3, 27)
    market = _market_context(spot_rate=1.00, volatility_30d_pct=3.0, pair_change_30d_pct=0.0, pair_change_90d_pct=0.0)
    exposure = _exposure(today, confidence=0.60)

    profile_without = _business_profile(target_budget_rate_enabled=False)
    profile_with = _business_profile(
        target_budget_rate_enabled=True,
        target_budget_rate=1.05,
        gross_margin_pct=25.0,
        minimum_margin_pct=10.0,
    )

    decision_without = build_hedge_decision(exposure, profile_without, market, today)
    decision_with = build_hedge_decision(exposure, profile_with, market, today)

    assert decision_with.budget_rate_triggered is True
    assert decision_with.final_hedge_ratio > decision_without.final_hedge_ratio


def test_select_instrument() -> None:
    assert select_instrument("committed", False) == "forward"
    assert select_instrument("forecast_high", False) == "layered_forward"
    assert select_instrument("forecast_medium", True) == "option_or_participating_forward"
    assert select_instrument("forecast_low", True) == "monitor_only"


def test_determine_execution_mode() -> None:
    assert determine_execution_mode("protect_margin", "committed", 1.0, False, True) == "defer_small_exposure"
    assert determine_execution_mode("balanced", "forecast_high", 0.7, True, False) == "auto_execute"
    assert determine_execution_mode("protect_margin", "committed", 0.95, False, False) == "auto_execute"
    assert determine_execution_mode("balanced", "forecast_low", 0.2, False, False) == "recommend"
    assert determine_execution_mode("balanced", "forecast_low", 0.0, False, False) == "monitor_only"


def test_tranche_schedule_generation() -> None:
    today = date(2026, 3, 27)

    committed = build_tranche_schedule(100_000.0, "committed", 20, today)
    assert len(committed) == 1
    assert committed[0]["target_execution_date"] == today.isoformat()
    assert "amount_foreign" in committed[0]
    assert "target_execution_date" in committed[0]

    two = build_tranche_schedule(100_000.01, "forecast_high", 90, today)
    three = build_tranche_schedule(100_000.0, "forecast_high", 180, today)
    four = build_tranche_schedule(100_000.0, "forecast_high", 365, today)

    assert len(two) == 2
    assert len(three) == 3
    assert len(four) == 4
    assert all("amount_foreign" in tranche and "target_execution_date" in tranche for tranche in two)
    assert sum(tranche["amount_foreign"] for tranche in two) == 100_000.01
    assert all(isinstance(tranche["target_execution_date"], str) for tranche in four)


def test_margin_trigger_does_not_fire_without_linked_revenue() -> None:
    today = date(2026, 3, 27)
    profile = _business_profile(
        minimum_margin_pct=15.0,
        worst_case_rate_enabled=True,
        worst_case_rate=0.80,
    )
    market = _market_context(spot_rate=1.10)
    exposure = _exposure(
        today,
        source_type="budget_forecast",
        confidence=0.60,
        amount=500_000.0,
        due_date=today + timedelta(days=120),
        linked_revenue_home_ccy=None,
    )

    decision = build_hedge_decision(exposure, profile, market, today)
    assert decision.margin_triggered is False


def test_build_hedge_decision_returns_dataclass() -> None:
    today = date(2026, 3, 27)
    decision = build_hedge_decision(
        _exposure(today),
        _business_profile(),
        _market_context(),
        today,
    )
    assert isinstance(decision, HedgeDecision)


def test_exposure_reference_rate_alias() -> None:
    today = date(2026, 3, 27)
    exposure = _exposure(today, rate=1.2345)
    assert exposure.rate == 1.2345
    assert exposure.reference_rate == exposure.rate
