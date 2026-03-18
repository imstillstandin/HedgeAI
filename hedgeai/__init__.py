"""Core package exports for FX Risk Radar domain logic."""

from importlib import import_module

__all__ = [
    "validate_dataframe",
    "clean_dataframe",
    "aggregate_exposures",
    "add_scenarios",
    "scenario_analysis",
    "suggest_hedge_range",
    "calculate_health_score",
    "format_currency",
    "generate_summary_text",
    "build_demo_data",
]

_EXPORT_MAP = {
    "validate_dataframe": ("hedgeai.data_processing", "validate_dataframe"),
    "clean_dataframe": ("hedgeai.data_processing", "clean_dataframe"),
    "aggregate_exposures": ("hedgeai.data_processing", "aggregate_exposures"),
    "add_scenarios": ("hedgeai.data_processing", "add_scenarios"),
    "scenario_analysis": ("hedgeai.risk", "scenario_analysis"),
    "suggest_hedge_range": ("hedgeai.risk", "suggest_hedge_range"),
    "calculate_health_score": ("hedgeai.risk", "calculate_health_score"),
    "format_currency": ("hedgeai.presentation", "format_currency"),
    "generate_summary_text": ("hedgeai.presentation", "generate_summary_text"),
    "build_demo_data": ("hedgeai.presentation", "build_demo_data"),
}


def __getattr__(name):
    if name not in _EXPORT_MAP:
        raise AttributeError(f"module 'hedgeai' has no attribute '{name}'")

    module_name, attr_name = _EXPORT_MAP[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
