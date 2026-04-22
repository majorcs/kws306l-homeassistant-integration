"""Constants for the KWS306L integration."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, Platform

DOMAIN = "kws306l"
PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR,)

CONF_PROTOCOL = "protocol"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SERIAL_PORT = "serial_port"
CONF_SLAVE_ID = "slave_id"

DEFAULT_NAME = "KWS306L"
DEFAULT_PORT = 502
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_SERIAL_BAUDRATE = 9600
DEFAULT_SLAVE_ID = 1
DEFAULT_TIMEOUT = 3.0

PROTOCOL_TCP = "tcp"
PROTOCOL_SERIAL = "serial"
SUPPORTED_PROTOCOLS = (PROTOCOL_TCP, PROTOCOL_SERIAL)

MANUFACTURER = "KWS"
MODEL = "KWS-306L"
VERSION = "2026.04.22.1"


def build_unique_id(data: dict[str, object]) -> str:
    """Build a stable config entry unique ID."""
    protocol = str(data[CONF_PROTOCOL])
    slave_id = int(data[CONF_SLAVE_ID])

    if protocol == PROTOCOL_TCP:
        host = str(data[CONF_HOST]).strip().lower()
        port = int(data[CONF_PORT])
        return f"{protocol}:{host}:{port}:{slave_id}"

    serial_port = str(data[CONF_SERIAL_PORT]).strip()
    return f"{protocol}:{serial_port}:{slave_id}"


def build_entry_title(data: dict[str, object]) -> str:
    """Build a friendly config entry title."""
    custom_name = str(data.get(CONF_NAME, "")).strip()
    if custom_name:
        return custom_name

    protocol = str(data[CONF_PROTOCOL])
    slave_id = int(data[CONF_SLAVE_ID])
    if protocol == PROTOCOL_TCP:
        return f"{DEFAULT_NAME} {data[CONF_HOST]}:{data[CONF_PORT]} (ID {slave_id})"

    return f"{DEFAULT_NAME} {data[CONF_SERIAL_PORT]} (ID {slave_id})"

