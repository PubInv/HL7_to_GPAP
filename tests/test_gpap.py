from hl7_to_gpap.gpap import (
    parse_alarm,
    parse_operator_response,
    render_alarm,
    render_operator_response,
)
from hl7_to_gpap.models import GpapAlarm, GpapOperatorResponse


def test_alarm_round_trip() -> None:
    alarm = GpapAlarm(
        severity=5,
        alarm_id="abc123",
        alarm_type="101",
        description="My hair is on fire",
    )
    encoded = render_alarm(alarm)
    parsed = parse_alarm(encoded)

    assert encoded == "a5{abc123}[101]My hair is on fire"
    assert parsed.severity == 5
    assert parsed.alarm_id == "abc123"
    assert parsed.alarm_type == "101"
    assert parsed.description == "My hair is on fire"


def test_operator_response_round_trip() -> None:
    response = GpapOperatorResponse(
        action="a",
        alarm_id="abc123",
        operator="sai",
        at="20260403120000",
    )
    encoded = render_operator_response(response)
    parsed = parse_operator_response(encoded)

    assert encoded == "oa{abc123}|sai|20260403120000"
    assert parsed.action == "a"
    assert parsed.alarm_id == "abc123"
    assert parsed.operator == "sai"
    assert parsed.at == "20260403120000"