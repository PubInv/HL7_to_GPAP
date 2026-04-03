from __future__ import annotations

from datetime import datetime, timezone
import re

from .models import GpapAlarm, GpapOperatorResponse


def _now_hl7_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _split_segments(er7_message: str) -> list[list[str]]:
    raw_segments = [
        line.strip()
        for chunk in er7_message.replace("\n", "\r").split("\r")
        for line in [chunk]
        if line.strip()
    ]
    return [segment.split("|") for segment in raw_segments]


def _get_first_segment(segments: list[list[str]], name: str) -> list[str] | None:
    for segment in segments:
        if segment and segment[0] == name:
            return segment
    return None


def _get_all_segments(segments: list[list[str]], name: str) -> list[list[str]]:
    return [segment for segment in segments if segment and segment[0] == name]


def _field(segment: list[str] | None, idx: int) -> str:
    if segment is None:
        return ""
    if idx >= len(segment):
        return ""
    return segment[idx].strip()


def _extract_message_type(msh: list[str] | None) -> str:
    return _field(msh, 8)


def _extract_control_id(msh: list[str] | None) -> str | None:
    value = _field(msh, 9)
    return value or None


def _extract_source(msh: list[str] | None) -> str | None:
    value = _field(msh, 2)
    return value or None


def _extract_patient_id(pid: list[str] | None) -> str | None:
    value = _field(pid, 3)
    return value or None


def _extract_observation_code(obx: list[str] | None) -> str | None:
    value = _field(obx, 3)
    return value or None


def _extract_observation_value(obx: list[str] | None) -> str | None:
    value = _field(obx, 5)
    return value or None


def _extract_abnormal_flag(obx: list[str] | None) -> str | None:
    value = _field(obx, 8)
    return value or None


def _extract_note(ntes: list[list[str]]) -> str | None:
    for nte in ntes:
        value = _field(nte, 3)
        if value:
            return value
    return None


def _severity_from_abnormal_flag(flag: str | None) -> int:
    if not flag:
        return 1

    flag = flag.strip().upper()

    mapping = {
        "N": 1,
        "L": 2,
        "LL": 3,
        "W": 3,
        "A": 4,
        "H": 4,
        "HH": 5,
        "AA": 5,
    }
    return mapping.get(flag, 3)


def _alarm_type_from_observation_code(observation_code: str | None) -> str | None:
    if not observation_code:
        return None

    match = re.search(r"(\d+)", observation_code)
    return match.group(1) if match else None


def hl7_er7_to_gpap_alarm(er7_message: str) -> GpapAlarm:
    """
    Narrow MVP mapping.

    Supported shape:
    - HL7 v2 ER7 text
    - first OBX segment is treated as the alarm-carrying observation
    - OBX-8 abnormal flag drives severity
    - MSH-10 becomes alarm_id
    - NTE-3 or OBX-5 becomes description
    - numeric portion of OBX-3 becomes optional alarm_type
    """
    segments = _split_segments(er7_message)

    msh = _get_first_segment(segments, "MSH")
    pid = _get_first_segment(segments, "PID")
    obx = _get_first_segment(segments, "OBX")
    ntes = _get_all_segments(segments, "NTE")

    if msh is None:
        raise ValueError("HL7 message missing MSH segment")
    if obx is None:
        raise ValueError("HL7 message missing OBX segment")

    message_type = _extract_message_type(msh)
    if not message_type:
        raise ValueError("HL7 message missing MSH-9 message type")

    description = _extract_note(ntes) or _extract_observation_value(obx) or "HL7 alarm"
    abnormal_flag = _extract_abnormal_flag(obx)
    observation_code = _extract_observation_code(obx)

    return GpapAlarm(
        severity=_severity_from_abnormal_flag(abnormal_flag),
        description=description,
        alarm_id=_extract_control_id(msh),
        alarm_type=_alarm_type_from_observation_code(observation_code),
        source=_extract_source(msh),
        patient_id=_extract_patient_id(pid),
        extra={
            "hl7_message_type": message_type,
            "observation_code": observation_code,
            "observation_value": _extract_observation_value(obx),
            "abnormal_flag": abnormal_flag,
        },
    )


def gpap_alarm_to_hl7_zgp(alarm: GpapAlarm) -> str:
    """
    Custom Z message for MVP transport of GPAP semantics into HL7-shaped text.
    """
    message_control_id = alarm.alarm_id or f"gpap-{_now_hl7_timestamp()}"
    timestamp = _now_hl7_timestamp()

    msh = (
        f"MSH|^~\\&|GPAP_BRIDGE|PubInv|HL7_RECEIVER|PubInv|{timestamp}"
        f"||ZGP^Z01|{message_control_id}|P|2.5"
    )
    zal = (
        f"ZAL|{alarm.alarm_id or ''}|{alarm.severity}|{alarm.alarm_type or ''}"
        f"|{alarm.source or ''}|{alarm.patient_id or ''}|{alarm.description}"
    )
    return "\r".join([msh, zal]) + "\r"


def gpap_operator_response_to_hl7_zgp_response(
    response: GpapOperatorResponse,
) -> str:
    timestamp = _now_hl7_timestamp()
    message_control_id = response.alarm_id or f"resp-{timestamp}"

    msh = (
        f"MSH|^~\\&|GPAP_BRIDGE|PubInv|HL7_RECEIVER|PubInv|{timestamp}"
        f"||ZGP^Z02|{message_control_id}|P|2.5"
    )
    zop = (
        f"ZOP|{response.alarm_id or ''}|{response.action}"
        f"|{response.operator or ''}|{response.at or timestamp}"
    )
    return "\r".join([msh, zop]) + "\r"