from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .bridge import (
    gpap_alarm_to_hl7_zgp,
    gpap_operator_response_to_hl7_zgp_response,
    hl7_er7_to_gpap_alarm,
)
from .gpap import parse_alarm, parse_operator_response, render_alarm
from .mqtt import publish_alarm


def _read_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hl7-to-gpap",
        description="Narrow MVP bridge between HL7 ER7 and GPAP",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    p1 = subparsers.add_parser("hl7-to-gpap", help="Convert HL7 ER7 into a GPAP alarm")
    p1.add_argument("--file", help="Path to HL7 ER7 file. Defaults to stdin")

    p2 = subparsers.add_parser("gpap-to-hl7", help="Convert GPAP alarm into HL7 ZGP")
    p2.add_argument("--alarm", required=True, help="GPAP alarm string")

    p3 = subparsers.add_parser(
        "response-to-hl7",
        help="Convert GPAP operator response into HL7 ZGP response message",
    )
    p3.add_argument("--response", required=True, help="GPAP operator response string")

    p4 = subparsers.add_parser(
        "publish-hl7",
        help="Convert HL7 ER7 into GPAP and publish to MQTT",
    )
    p4.add_argument("--file", help="Path to HL7 ER7 file. Defaults to stdin")
    p4.add_argument("--host", required=True, help="MQTT broker host")
    p4.add_argument("--port", type=int, default=1883)
    p4.add_argument("--topic", default="adam/in/alarms")
    p4.add_argument("--username")
    p4.add_argument("--password")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "hl7-to-gpap":
        er7 = _read_text(args.file)
        alarm = hl7_er7_to_gpap_alarm(er7)
        print(render_alarm(alarm))
        return 0

    if args.command == "gpap-to-hl7":
        alarm = parse_alarm(args.alarm)
        print(gpap_alarm_to_hl7_zgp(alarm).replace("\r", "\n").rstrip())
        return 0

    if args.command == "response-to-hl7":
        response = parse_operator_response(args.response)
        print(gpap_operator_response_to_hl7_zgp_response(response).replace("\r", "\n").rstrip())
        return 0

    if args.command == "publish-hl7":
        er7 = _read_text(args.file)
        alarm = hl7_er7_to_gpap_alarm(er7)
        publish_alarm(
            alarm=alarm,
            host=args.host,
            port=args.port,
            topic=args.topic,
            username=args.username,
            password=args.password,
        )
        print(render_alarm(alarm))
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())