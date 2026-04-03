from __future__ import annotations

import re

from .models import GpapAlarm, GpapOperatorResponse

_ALARM_RE = re.compile(
    r"^a(?P<severity>[0-5])"
    r"(?:\{(?P<alarm_id>[^}]+)\})?"
    r"(?:\[(?P<alarm_type>[^\]]+)\])?"
    r"(?P<description>.+)$"
)

_OPERATOR_RE = re.compile(
    r"^o(?P<action>[asdc])"
    r"(?:\{(?P<alarm_id>[^}]+)\})?"
    r"(?:\|(?P<operator>[^|]*))?"
    r"(?:\|(?P<at>.*))?$"
)


def render_alarm(alarm: GpapAlarm) -> str:
    parts: list[str] = [f"a{alarm.severity}"]
    if alarm.alarm_id:
        parts.append(f"{{{alarm.alarm_id}}}")
    if alarm.alarm_type:
        parts.append(f"[{alarm.alarm_type}]")
    parts.append(alarm.description)
    return "".join(parts)


def parse_alarm(payload: str) -> GpapAlarm:
    payload = payload.strip()
    match = _ALARM_RE.match(payload)
    if not match:
        raise ValueError(f"invalid GPAP alarm: {payload!r}")

    return GpapAlarm(
        severity=int(match.group("severity")),
        alarm_id=match.group("alarm_id"),
        alarm_type=match.group("alarm_type"),
        description=match.group("description").strip(),
    )


def render_operator_response(response: GpapOperatorResponse) -> str:
    parts: list[str] = [f"o{response.action}"]
    if response.alarm_id:
        parts.append(f"{{{response.alarm_id}}}")
    if response.operator is not None or response.at is not None:
        parts.append("|")
        parts.append(response.operator or "")
    if response.at is not None:
        parts.append("|")
        parts.append(response.at)
    return "".join(parts)


def parse_operator_response(payload: str) -> GpapOperatorResponse:
    payload = payload.strip()
    match = _OPERATOR_RE.match(payload)
    if not match:
        raise ValueError(f"invalid GPAP operator response: {payload!r}")

    operator = match.group("operator")
    at = match.group("at")

    return GpapOperatorResponse(
        action=match.group("action"),
        alarm_id=match.group("alarm_id"),
        operator=operator if operator != "" else None,
        at=at if at != "" else None,
    )