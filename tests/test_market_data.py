"""Tests for market data abstraction and MarketContext building."""

from __future__ import annotations

from datetime import date
import sys
import types
from unittest.mock import Mock, patch

import pytest

# Allow importing fx_radar modules in minimal test environments.
sys.modules.setdefault("pandas", types.ModuleType("pandas"))
if "requests" not in sys.modules:
    requests_stub = types.ModuleType("requests")
    requests_stub.get = Mock()
    requests_stub.RequestException = Exception
    sys.modules["requests"] = requests_stub

from fx_radar.market_data import (  # noqa: E402
    FrankfurterProvider,
    MarketDataError,
    compute_pct_change,
    get_market_context,
    parse_currency_pair,
)
from fx_radar.models import MarketContext  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    get_market_context.cache_clear()


def test_pair_normalization_formats() -> None:
    assert parse_currency_pair("AUD/USD") == ("AUD", "USD")
    assert parse_currency_pair("AUD-USD") == ("AUD", "USD")
    assert parse_currency_pair("AUDUSD") == ("AUD", "USD")


def test_invalid_pair_format_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse_currency_pair("AUD_USD")


def test_provider_parses_latest_direct_rate() -> None:
    payload = {"base": "AUD", "rates": {"USD": 0.66}}
    provider = FrankfurterProvider()
    assert provider._extract_rate(payload, "AUD", "USD") == 0.66


def test_provider_rejects_non_positive_direct_rate() -> None:
    payload = {"base": "AUD", "rates": {"USD": 0.0}}
    provider = FrankfurterProvider()
    with pytest.raises(MarketDataError):
        provider._extract_rate(payload, "AUD", "USD")


def test_provider_inverts_when_reverse_orientation_returned() -> None:
    payload = {"base": "USD", "rates": {"AUD": 1.5}}
    provider = FrankfurterProvider()
    assert provider._extract_rate(payload, "AUD", "USD") == pytest.approx(2 / 3)


def test_market_context_creation_from_provider_methods() -> None:
    with patch.object(FrankfurterProvider, "get_latest_rate", return_value=0.66), patch.object(
        FrankfurterProvider,
        "get_historical_rate",
        side_effect=[0.60, 0.55],
    ):
        context = get_market_context("AUD/USD")

    assert isinstance(context, MarketContext)
    assert context.pair == "AUD/USD"
    assert context.spot_rate == 0.66
    assert context.pair_change_30d_pct == pytest.approx(compute_pct_change(0.66, 0.60))
    assert context.pair_change_90d_pct == pytest.approx(compute_pct_change(0.66, 0.55))
    assert context.forward_points == {30: 0.0, 90: 0.0, 180: 0.0, 365: 0.0}


def test_fallback_defaults_when_history_unavailable() -> None:
    with patch.object(FrankfurterProvider, "get_latest_rate", return_value=0.66), patch.object(
        FrankfurterProvider,
        "get_historical_rate",
        return_value=None,
    ):
        context = get_market_context("AUD/USD")

    assert context.volatility_30d_pct == 8.0
    assert context.volatility_90d_pct == 9.0
    assert context.pair_change_30d_pct == 0.0
    assert context.pair_change_90d_pct == 0.0


def test_provider_http_latest_parsing_with_mocked_requests() -> None:
    provider = FrankfurterProvider()
    fake_response = Mock()
    fake_response.json.return_value = {"base": "AUD", "rates": {"USD": 0.67}}
    fake_response.raise_for_status.return_value = None

    with patch("fx_radar.market_data.requests.get", return_value=fake_response) as mock_get:
        rate = provider.get_latest_rate("AUD", "USD")

    assert rate == 0.67
    assert mock_get.called
