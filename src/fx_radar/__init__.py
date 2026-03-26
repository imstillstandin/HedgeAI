"""FX Risk Radar domain package."""

from .alert_engine import generate_alerts
from .exposure_engine import aggregate_exposures
from .ingestion import clean_dataframe, validate_dataframe
from .presentation import format_currency, generate_summary_text
from .risk_engine import add_scenarios, calculate_health_score, scenario_analysis, suggest_hedge_range

__all__ = [
    "generate_alerts",
    "validate_dataframe",
    "clean_dataframe",
    "aggregate_exposures",
    "scenario_analysis",
    "suggest_hedge_range",
    "calculate_health_score",
    "add_scenarios",
    "format_currency",
    "generate_summary_text",
]
