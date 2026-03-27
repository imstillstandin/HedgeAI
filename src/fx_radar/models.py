"""Canonical data models for FX Risk Radar engines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class ExposureRecord:
    """Represents one FX exposure to be assessed for hedging.

    Notes:
        ``rate`` is the exposure-level booked/reference/budget rate recorded on
        the transaction. It is *not* the live market spot rate, which belongs to
        :class:`MarketContext`.
    """

    exposure_id: str
    currency: str
    amount: float
    exposure_type: str
    due_date: date
    rate: float
    source_type: str
    confidence: float
    linked_revenue_home_ccy: Optional[float] = None
    natural_offset_foreign: float = 0.0
    counterparty: Optional[str] = None
    source_system: Optional[str] = None
    source_id: Optional[str] = None
    status: str = "open"

    @property
    def reference_rate(self) -> float:
        """Backward-compatible alias for the exposure booked/reference rate."""
        return self.rate


@dataclass(frozen=True)
class BusinessProfile:
    """Business risk profile and policy constraints used by the engine."""

    home_currency: str
    industry_template: str
    risk_mode: str
    annual_revenue_home_ccy: float
    gross_margin_pct: float
    minimum_margin_pct: float
    max_hedge_tenor_days: int = 365
    allow_options: bool = False
    natural_hedge_enabled: bool = True
    target_budget_rate_enabled: bool = False
    target_budget_rate: Optional[float] = None
    worst_case_rate_enabled: bool = False
    worst_case_rate: Optional[float] = None


@dataclass(frozen=True)
class MarketContext:
    """FX market context for a currency pair."""

    pair: str
    spot_rate: float
    volatility_30d_pct: float
    volatility_90d_pct: float
    pair_change_30d_pct: float
    pair_change_90d_pct: float
    forward_points: dict[int, float]


@dataclass(frozen=True)
class HedgeDecision:
    """Deterministic hedge decision output for a single exposure."""

    exposure_id: str
    currency: str
    exposure_type: str
    certainty_class: str
    time_bucket: str
    days_to_settlement: int
    net_amount_foreign: float
    final_hedge_ratio: float
    hedge_amount_foreign: float
    instrument: str
    execution_mode: str
    margin_triggered: bool
    budget_rate_triggered: bool
    projected_margin_pct_under_stress: Optional[float]
    reason_codes: list[str]
    summary_text: str
    tranches: list[dict]
