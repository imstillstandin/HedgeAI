"""Canonical data models for FX Risk Radar engines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal, Optional

ExposureType = Literal["payable", "receivable"]


@dataclass(frozen=True)
class ExposureRecord:
    """Canonical exposure record shape used by the platform."""

    currency: str
    amount: float
    type: ExposureType
    due_date: date
    rate: float
    source_system: Optional[str] = None
    source_id: Optional[str] = None
    status: Optional[str] = None
