"""Deterministic hedge policy engine for SME FX exposures."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from .models import BusinessProfile, ExposureRecord, HedgeDecision, MarketContext

BASE_RATIOS: dict[str, float] = {
    "committed": 0.90,
    "forecast_high": 0.70,
    "forecast_medium": 0.45,
    "forecast_low": 0.20,
}

TIME_ADJUSTMENTS: dict[str, float] = {
    "0_30": 0.10,
    "31_90": 0.00,
    "91_180": -0.10,
    "181_365": -0.20,
    "365_plus": -1.00,
}

CLAMP_BANDS: dict[str, tuple[float, float]] = {
    "committed": (0.80, 1.00),
    "forecast_high": (0.50, 0.85),
    "forecast_medium": (0.25, 0.65),
    "forecast_low": (0.00, 0.35),
}


def _clamp(value: float, lower: float, upper: float) -> float:
    """Clamp ``value`` to the inclusive ``[lower, upper]`` range."""

    return max(lower, min(upper, value))


def classify_certainty(source_type: str, confidence: float) -> str:
    """Classify certainty of an exposure from source type and confidence score."""

    normalized = source_type.strip().lower()
    committed_sources = {
        "invoice",
        "signed_po",
        "loan_repayment",
        "executed_contract",
    }
    forecast_sources = {
        "subscription_forecast",
        "budget_forecast",
        "sales_pipeline_weighted",
        "inventory_plan",
    }
    if normalized in committed_sources:
        return "committed"
    if normalized in forecast_sources and confidence >= 0.70:
        return "forecast_high"
    if normalized in forecast_sources and confidence >= 0.40:
        return "forecast_medium"
    return "forecast_low"


def classify_time_bucket(days_to_settlement: int) -> str:
    """Map settlement horizon in days to a deterministic time bucket label."""

    if days_to_settlement <= 30:
        return "0_30"
    if days_to_settlement <= 90:
        return "31_90"
    if days_to_settlement <= 180:
        return "91_180"
    if days_to_settlement <= 365:
        return "181_365"
    return "365_plus"


def calculate_net_exposure(amount_foreign: float, natural_offset_foreign: float, enabled: bool) -> float:
    """Calculate net amount after natural hedge offsets, never below zero."""

    if not enabled:
        return max(0.0, amount_foreign)
    return max(0.0, amount_foreign - natural_offset_foreign)


def get_margin_adjustment(gross_margin_pct: float, minimum_margin_pct: float) -> float:
    """Return hedge ratio uplift based on available margin buffer."""

    buffer = gross_margin_pct - minimum_margin_pct
    if buffer <= 5:
        return 0.15
    if buffer <= 10:
        return 0.10
    if buffer <= 15:
        return 0.05
    return 0.00


def get_volatility_adjustment(volatility_30d_pct: float) -> float:
    """Return hedge ratio uplift based on 30-day volatility level."""

    if volatility_30d_pct >= 12:
        return 0.10
    if volatility_30d_pct >= 8:
        return 0.05
    return 0.00


def get_trend_adjustment(exposure_type: str, pair_change_30d_pct: float, pair_change_90d_pct: float) -> float:
    """Return hedge ratio uplift based on trend adversity for the exposure side."""

    adj = 0.0
    side = exposure_type.strip().lower()
    if side == "payable":
        if pair_change_30d_pct <= -3.0:
            adj += 0.05
        if pair_change_90d_pct <= -5.0:
            adj += 0.05
    elif side == "receivable":
        if pair_change_30d_pct >= 3.0:
            adj += 0.05
        if pair_change_90d_pct >= 5.0:
            adj += 0.05
    return min(adj, 0.10)


def calculate_final_hedge_ratio(
    certainty_class: str,
    time_bucket: str,
    business_profile: BusinessProfile,
    market_context: MarketContext,
    exposure_type: str,
) -> float:
    """Calculate unclipped policy ratio and clamp to certainty-specific guardrails."""

    base = BASE_RATIOS[certainty_class]
    ratio = (
        base
        + TIME_ADJUSTMENTS[time_bucket]
        + get_margin_adjustment(
            gross_margin_pct=business_profile.gross_margin_pct,
            minimum_margin_pct=business_profile.minimum_margin_pct,
        )
        + get_volatility_adjustment(market_context.volatility_30d_pct)
        + get_trend_adjustment(
            exposure_type,
            market_context.pair_change_30d_pct,
            market_context.pair_change_90d_pct,
        )
    )
    lower, upper = CLAMP_BANDS[certainty_class]
    return _clamp(ratio, lower, upper)


def evaluate_margin_trigger(
    exposure: ExposureRecord,
    business_profile: BusinessProfile,
    market_context: MarketContext,
    net_amount_foreign: float,
) -> tuple[bool, Optional[float]]:
    """Stress-test margin and indicate whether a defensive hedge floor must apply."""

    if not (
        business_profile.worst_case_rate_enabled
        and business_profile.worst_case_rate is not None
        and exposure.linked_revenue_home_ccy is not None
        and exposure.exposure_type == "payable"
    ):
        return (False, None)

    current_rate = market_context.spot_rate
    worst_rate = business_profile.worst_case_rate
    home_cost_now = net_amount_foreign / current_rate
    home_cost_worst = net_amount_foreign / worst_rate
    revenue = exposure.linked_revenue_home_ccy
    projected_margin_pct = ((revenue - home_cost_worst) / revenue) * 100.0

    _ = home_cost_now
    return (projected_margin_pct < business_profile.minimum_margin_pct, projected_margin_pct)


def evaluate_budget_rate_trigger(exposure_type: str, current_rate: float, target_budget_rate: float) -> bool:
    """Evaluate if budget rate threshold is favorable for opportunistic hedge increase."""

    side = exposure_type.strip().lower()
    if side == "payable":
        return current_rate <= target_budget_rate
    if side == "receivable":
        return current_rate >= target_budget_rate
    return False


def select_instrument(certainty_class: str, allow_options: bool) -> str:
    """Select instrument family from certainty class and options policy."""

    if certainty_class == "committed":
        return "forward"
    if certainty_class in {"forecast_high", "forecast_medium"}:
        if allow_options:
            return "option_or_participating_forward"
        return "layered_forward"
    return "monitor_only"


def build_tranche_schedule(
    hedge_amount_foreign: float,
    certainty_class: str,
    days_to_settlement: int,
    today: date,
) -> list[dict]:
    """Create deterministic tranche dates and sizes."""

    if hedge_amount_foreign <= 0:
        return []

    if certainty_class == "committed":
        return [
            {
                "amount_foreign": hedge_amount_foreign,
                "target_execution_date": today.isoformat(),
            }
        ]

    if days_to_settlement <= 90:
        tranche_count = 2
    elif days_to_settlement <= 180:
        tranche_count = 3
    else:
        tranche_count = 4

    interval_days = max(1, days_to_settlement // tranche_count if days_to_settlement > 0 else 1)
    base_amount = round(hedge_amount_foreign / tranche_count, 2)
    remaining_amount = hedge_amount_foreign

    tranches: list[dict] = []
    for i in range(tranche_count):
        tranche_amount = base_amount if i < tranche_count - 1 else remaining_amount
        remaining_amount -= tranche_amount
        tranches.append(
            {
                "amount_foreign": tranche_amount,
                "target_execution_date": (today + timedelta(days=interval_days * i)).isoformat(),
            }
        )
    return tranches


def determine_execution_mode(
    risk_mode: str,
    certainty_class: str,
    final_ratio: float,
    margin_triggered: bool,
    small_exposure: bool,
) -> str:
    """Choose execution mode according to policy priority rules."""

    if small_exposure:
        return "defer_small_exposure"
    if margin_triggered:
        return "auto_execute"
    if risk_mode == "protect_margin" and certainty_class == "committed" and final_ratio >= 0.90:
        return "auto_execute"
    if final_ratio > 0:
        return "recommend"
    return "monitor_only"


def _is_small_exposure(hedge_amount: float, annual_revenue: float) -> bool:
    """Check whether a hedge amount falls below size threshold for the business."""

    if annual_revenue < 3_000_000:
        return hedge_amount < 10_000
    if annual_revenue < 15_000_000:
        return hedge_amount < 25_000
    return hedge_amount < 50_000


def build_hedge_decision(
    exposure: ExposureRecord,
    business_profile: BusinessProfile,
    market_context: MarketContext,
    today: date,
) -> HedgeDecision:
    """Build a deterministic hedge decision for one exposure."""

    days_to_settlement = (exposure.due_date - today).days
    certainty_class = classify_certainty(exposure.source_type, exposure.confidence)
    time_bucket = classify_time_bucket(days_to_settlement)
    net_amount = calculate_net_exposure(
        amount_foreign=exposure.amount,
        natural_offset_foreign=exposure.natural_offset_foreign,
        enabled=business_profile.natural_hedge_enabled,
    )

    final_ratio = calculate_final_hedge_ratio(
        certainty_class=certainty_class,
        time_bucket=time_bucket,
        business_profile=business_profile,
        market_context=market_context,
        exposure_type=exposure.exposure_type,
    )

    margin_triggered, projected_margin = evaluate_margin_trigger(
        exposure=exposure,
        business_profile=business_profile,
        market_context=market_context,
        net_amount_foreign=net_amount,
    )

    if certainty_class == "committed" and days_to_settlement <= 14:
        final_ratio = 1.0

    margin_floor_required = margin_triggered
    if margin_floor_required:
        final_ratio = max(final_ratio, 0.90)

    budget_triggered = False
    if (
        business_profile.target_budget_rate_enabled
        and business_profile.target_budget_rate is not None
        and evaluate_budget_rate_trigger(
            exposure_type=exposure.exposure_type,
            current_rate=market_context.spot_rate,
            target_budget_rate=business_profile.target_budget_rate,
        )
    ):
        budget_triggered = True
        final_ratio += 0.10

    lower, upper = CLAMP_BANDS[certainty_class]
    final_ratio = _clamp(final_ratio, lower, upper)
    if margin_floor_required:
        final_ratio = max(final_ratio, 0.90)

    hedge_amount = net_amount * final_ratio
    instrument = select_instrument(certainty_class, business_profile.allow_options)
    small_exposure = _is_small_exposure(hedge_amount, business_profile.annual_revenue_home_ccy)
    execution_mode = determine_execution_mode(
        risk_mode=business_profile.risk_mode,
        certainty_class=certainty_class,
        final_ratio=final_ratio,
        margin_triggered=margin_triggered,
        small_exposure=small_exposure,
    )

    tranches = build_tranche_schedule(
        hedge_amount_foreign=hedge_amount,
        certainty_class=certainty_class,
        days_to_settlement=days_to_settlement,
        today=today,
    )

    reason_codes: list[str] = []
    if margin_triggered:
        reason_codes.append("margin_protection")
    if budget_triggered:
        reason_codes.append("budget_rate_opportunity")
    if certainty_class == "committed" and days_to_settlement <= 14:
        reason_codes.append("near_term_committed_force_full")
    if not reason_codes:
        reason_codes.append("policy_base_case")

    summary = (
        f"{exposure.exposure_id}: hedge {final_ratio:.0%} ({instrument}) "
        f"for net {net_amount:.2f} {exposure.currency}."
    )

    return HedgeDecision(
        exposure_id=exposure.exposure_id,
        currency=exposure.currency,
        exposure_type=exposure.exposure_type,
        certainty_class=certainty_class,
        time_bucket=time_bucket,
        days_to_settlement=days_to_settlement,
        net_amount_foreign=net_amount,
        final_hedge_ratio=final_ratio,
        hedge_amount_foreign=hedge_amount,
        instrument=instrument,
        execution_mode=execution_mode,
        margin_triggered=margin_triggered,
        budget_rate_triggered=budget_triggered,
        projected_margin_pct_under_stress=projected_margin,
        reason_codes=reason_codes,
        summary_text=summary,
        tranches=tranches,
    )


def build_portfolio_hedge_decisions(
    exposures: list[ExposureRecord],
    business_profile: BusinessProfile,
    market_context: MarketContext,
    today: date,
) -> list[HedgeDecision]:
    """Build deterministic hedge decisions for all supplied exposures."""

    return [
        build_hedge_decision(
            exposure=exposure,
            business_profile=business_profile,
            market_context=market_context,
            today=today,
        )
        for exposure in exposures
    ]
