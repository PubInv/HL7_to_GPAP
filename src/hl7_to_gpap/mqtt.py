from __future__ import annotations

from .gpap import render_alarm
from .models import GpapAlarm

try:
    import paho.mqtt.client as mqtt
except ImportError as exc:
    mqtt = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def publish_alarm(
    alarm: GpapAlarm,
    host: str,
    port: int = 1883,
    topic: str = "adam/in/alarms",
    username: str | None = None,
    password: str | None = None,
    keepalive: int = 60,
) -> None:
    if mqtt is None:
        raise RuntimeError(
            "paho-mqtt is not installed. Install project dependencies first."
        ) from _IMPORT_ERROR

    client = mqtt.Client()
    if username is not None:
        client.username_pw_set(username=username, password=password)

    client.connect(host, port, keepalive)
    payload = render_alarm(alarm)
    info = client.publish(topic, payload=payload, qos=0, retain=False)
    info.wait_for_publish()
    client.disconnect()