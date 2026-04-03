from hl7_to_gpap.bridge import (
    gpap_alarm_to_hl7_zgp,
    gpap_operator_response_to_hl7_zgp_response,
    hl7_er7_to_gpap_alarm,
)
from hl7_to_gpap.gpap import render_alarm
from hl7_to_gpap.models import GpapAlarm, GpapOperatorResponse


def test_hl7_to_gpap_alarm() -> None:
    msg = (
        "MSH|^~\\&|MONITOR_APP|WARD1|ADAM|PUBINV|20260403113000||ORU^R01|MSG123|P|2.5\r"
        "PID|1||PAT42^^^HOSP^MR||Doe^Jane\r"
        "OBR|1||ORDER1|15074^Pulse^LN\r"
        "OBX|1|NM|15074^Pulse^LN||180|bpm|60-100|HH|||F\r"
        "NTE|1||Pulse exceeded high-high threshold\r"
    )

    alarm = hl7_er7_to_gpap_alarm(msg)

    assert alarm.severity == 5
    assert alarm.alarm_id == "MSG123"
    assert alarm.patient_id == "PAT42^^^HOSP^MR"
    assert alarm.alarm_type == "15074"
    assert alarm.description == "Pulse exceeded high-high threshold"
    assert render_alarm(alarm) == "a5{MSG123}[15074]Pulse exceeded high-high threshold"


def test_gpap_alarm_to_custom_hl7() -> None:
    alarm = GpapAlarm(
        severity=4,
        alarm_id="MSG123",
        alarm_type="15074",
        description="High pulse",
        source="MONITOR_APP",
        patient_id="PAT42",
    )

    hl7 = gpap_alarm_to_hl7_zgp(alarm)

    assert "ZGP^Z01" in hl7
    assert "ZAL|MSG123|4|15074|MONITOR_APP|PAT42|High pulse" in hl7


def test_gpap_response_to_custom_hl7() -> None:
    response = GpapOperatorResponse(
        action="c",
        alarm_id="MSG123",
        operator="sai",
        at="20260403120000",
    )

    hl7 = gpap_operator_response_to_hl7_zgp_response(response)

    assert "ZGP^Z02" in hl7
    assert "ZOP|MSG123|c|sai|20260403120000" in hl7