from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GpapAlarm:
    severity: int
    description: str
    alarm_id: str | None = None
    alarm_type: str | None = None
    source: str | None = None
    patient_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (0 <= self.severity <= 5):
            raise ValueError("severity must be between 0 and 5")
        self.description = self.description.strip()
        if not self.description:
            raise ValueError("description cannot be empty")


@dataclass(slots=True)
class GpapOperatorResponse:
    action: str
    alarm_id: str | None = None
    operator: str | None = None
    at: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        allowed = {"a", "s", "d", "c"}
        if self.action not in allowed:
            raise ValueError(f"action must be one of {sorted(allowed)}")