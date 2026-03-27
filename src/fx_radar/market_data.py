"""Market data abstraction for FX pair context retrieval."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta
from functools import lru_cache
import re
from typing import Optional

import requests

from .models import MarketContext

DEFAULT_VOL_30D = 8.0
DEFAULT_VOL_90D = 9.0
DEFAULT_CHANGE = 0.0


class MarketDataError(RuntimeError):
    """Raised when market data cannot be fetched or parsed."""


def parse_currency_pair(pair: str) -> tuple[str, str]:
    """Parse pair strings like AUD/USD, AUD-USD, or AUDUSD into (base, quote)."""

    normalized = pair.strip().upper()
    if "/" in normalized:
        parts = normalized.split("/")
    elif "-" in normalized:
        parts = normalized.split("-")
    elif re.fullmatch(r"[A-Z]{6}", normalized):
        parts = [normalized[:3], normalized[3:]]
    else:
        raise ValueError(
            "Invalid pair format. Use formats like 'AUD/USD', 'AUD-USD', or 'AUDUSD'."
        )

    if len(parts) != 2 or any(not re.fullmatch(r"[A-Z]{3}", p) for p in parts):
        raise ValueError(
            "Invalid pair format. Use formats like 'AUD/USD', 'AUD-USD', or 'AUDUSD'."
        )
    return parts[0], parts[1]


def build_default_forward_points() -> dict[int, float]:
    """Return default MVP forward points map."""

    return {30: 0.0, 90: 0.0, 180: 0.0, 365: 0.0}


def compute_pct_change(current_rate: float, historical_rate: float) -> float:
    """Compute percentage change from historical to current rate."""

    if historical_rate <= 0:
        raise ValueError("Historical rate must be positive for percentage change calculation.")
    return ((current_rate - historical_rate) / historical_rate) * 100.0


class FXMarketDataProvider(ABC):
    """Provider interface for FX market data sources."""

    @abstractmethod
    def get_latest_rate(self, base: str, quote: str) -> float:
        """Return latest spot for base/quote."""

    @abstractmethod
    def get_historical_rate(self, base: str, quote: str, as_of: date) -> Optional[float]:
        """Return historical spot for base/quote on date, or None if unavailable."""


class FrankfurterProvider(FXMarketDataProvider):
    """Frankfurter.app-backed FX market data provider."""

    base_url = "https://api.frankfurter.app"

    def _extract_rate(self, payload: dict, base: str, quote: str) -> float:
        """Extract direct or reversed rate from provider payload."""

        rates = payload.get("rates") or {}
        if quote in rates:
            rate = float(rates[quote])
            if rate <= 0:
                raise MarketDataError("Provider returned non-positive direct rate.")
            return rate

        response_base = str(payload.get("base", "")).upper()
        if response_base == quote and base in rates:
            reverse_rate = float(rates[base])
            if reverse_rate <= 0:
                raise MarketDataError("Provider returned non-positive reverse rate.")
            return 1.0 / reverse_rate

        raise MarketDataError("Requested rate not found in provider response.")

    def get_latest_rate(self, base: str, quote: str) -> float:
        """Fetch latest FX spot from Frankfurter."""

        url = f"{self.base_url}/latest"
        params = {"from": base, "to": quote}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            return self._extract_rate(payload, base, quote)
        except requests.RequestException as exc:
            raise MarketDataError(f"Failed to fetch latest FX rate for {base}/{quote}: {exc}") from exc
        except (TypeError, ValueError, KeyError) as exc:
            raise MarketDataError("Invalid latest-rate payload from provider.") from exc

    def get_historical_rate(self, base: str, quote: str, as_of: date) -> Optional[float]:
        """Fetch historical FX spot from Frankfurter or return None if unavailable."""

        url = f"{self.base_url}/{as_of.isoformat()}"
        params = {"from": base, "to": quote}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            return self._extract_rate(payload, base, quote)
        except (requests.RequestException, TypeError, ValueError, KeyError, MarketDataError):
            return None


def _build_provider(provider_name: str) -> FXMarketDataProvider:
    """Build provider instance by name."""

    name = provider_name.strip().lower()
    if name == "frankfurter":
        return FrankfurterProvider()
    raise ValueError(f"Unsupported market data provider: {provider_name}")


@lru_cache(maxsize=64)
def get_market_context(pair: str, provider_name: str = "frankfurter") -> MarketContext:
    """Fetch/derive a MarketContext for a pair via selected provider."""

    base, quote = parse_currency_pair(pair)
    normalized_pair = f"{base}/{quote}"
    provider = _build_provider(provider_name)

    spot = provider.get_latest_rate(base, quote)

    hist_30 = provider.get_historical_rate(base, quote, date.today() - timedelta(days=30))
    hist_90 = provider.get_historical_rate(base, quote, date.today() - timedelta(days=90))

    change_30 = compute_pct_change(spot, hist_30) if hist_30 else DEFAULT_CHANGE
    change_90 = compute_pct_change(spot, hist_90) if hist_90 else DEFAULT_CHANGE

    return MarketContext(
        pair=normalized_pair,
        spot_rate=spot,
        volatility_30d_pct=DEFAULT_VOL_30D,
        volatility_90d_pct=DEFAULT_VOL_90D,
        pair_change_30d_pct=change_30,
        pair_change_90d_pct=change_90,
        forward_points=build_default_forward_points(),
    )
