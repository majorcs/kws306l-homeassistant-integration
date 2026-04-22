"""Tests for Modbus helpers."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from custom_components.kws306l.const import (
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_PORT,
    CONF_SLAVE_ID,
    build_entry_title,
    build_unique_id,
)
from custom_components.kws306l.modbus import KwsConnectionParams, KwsModbusClient, KwsModbusError
from custom_components.kws306l.register_map import RegisterBlock


class FakeResult:
    """Small fake pymodbus result object."""

    def __init__(self, registers, *, is_error: bool = False) -> None:
        self.registers = registers
        self._is_error = is_error

    def isError(self) -> bool:
        return self._is_error


def test_build_unique_id_for_tcp():
    """TCP IDs should be stable."""
    assert (
        build_unique_id(
            {
                CONF_PROTOCOL: "tcp",
                "host": "EXAMPLE.local",
                "port": 502,
                CONF_SLAVE_ID: 7,
            }
        )
        == "tcp:example.local:502:7"
    )


def test_build_entry_title_for_serial():
    """Serial titles should fall back to a deterministic name."""
    assert (
        build_entry_title(
            {
                CONF_PROTOCOL: "serial",
                CONF_SERIAL_PORT: "/dev/ttyUSB0",
                CONF_SLAVE_ID: 9,
                CONF_SCAN_INTERVAL: 30,
            }
        )
        == "KWS306L /dev/ttyUSB0 (ID 9)"
    )


def test_read_blocks_sync_combines_registers(hass):
    """Contiguous reads should be flattened into an address map."""
    client = KwsModbusClient(
        hass,
        KwsConnectionParams(
            protocol="tcp",
            host="192.0.2.10",
            port=502,
            slave_id=1,
        ),
    )
    fake_client = Mock()
    client._ensure_connected = Mock(return_value=fake_client)
    client._read_registers = Mock(
        side_effect=[
            FakeResult([0x0203]),
            FakeResult([22000, 22100, 22200]),
        ]
    )

    result = client._read_blocks_sync(
        (
            RegisterBlock(start=12, count=1),
            RegisterBlock(start=14, count=3),
        )
    )

    assert result == {
        12: 0x0203,
        14: 22000,
        15: 22100,
        16: 22200,
    }


def test_read_blocks_sync_raises_on_modbus_error(hass):
    """Modbus failures should be surfaced as KwsModbusError."""
    client = KwsModbusClient(
        hass,
        KwsConnectionParams(
            protocol="tcp",
            host="192.0.2.10",
            port=502,
            slave_id=1,
        ),
    )
    client._ensure_connected = Mock(return_value=Mock())
    client._read_registers = Mock(return_value=FakeResult([], is_error=True))
    client._close_sync = Mock()

    with pytest.raises(KwsModbusError):
        client._read_blocks_sync((RegisterBlock(start=14, count=1),))

    client._close_sync.assert_called_once()

