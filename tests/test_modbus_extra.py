"""Extra branch coverage for Modbus transport helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.kws306l.modbus import KwsConnectionParams, KwsModbusClient, KwsModbusError


async def test_async_validate_connection_uses_measurement_register(hass):
    """Validation should read the first measurement register block."""
    client = KwsModbusClient(hass, KwsConnectionParams(protocol="tcp", host="192.0.2.40", slave_id=1))
    client.async_read_blocks = AsyncMock(return_value={14: 22000})

    await client.async_validate_connection()

    client.async_read_blocks.assert_awaited_once()


async def test_async_close_uses_executor(hass):
    """async_close should delegate to the executor helper."""
    client = KwsModbusClient(hass, KwsConnectionParams(protocol="tcp", host="192.0.2.41", slave_id=1))
    with patch.object(hass, "async_add_executor_job", AsyncMock()) as executor_job:
        await client.async_close()

    executor_job.assert_awaited_once()


def test_connection_params_from_mapping_supports_serial():
    """Serial mappings should populate the serial port field."""
    params = KwsConnectionParams.from_mapping(
        {
            "protocol": "serial",
            "serial_port": "/dev/ttyUSB1",
            "slave_id": 5,
            "scan_interval": 30,
        }
    )

    assert params.protocol == "serial"
    assert params.serial_port == "/dev/ttyUSB1"
    assert params.port == 502


def test_get_client_creates_tcp_client(hass):
    """TCP clients should be created with the TCP constructor."""
    with patch("custom_components.kws306l.modbus.ModbusTcpClient", return_value=Mock()) as tcp_client:
        client = KwsModbusClient(hass, KwsConnectionParams(protocol="tcp", host="192.0.2.42", port=1502, slave_id=2))
        assert client._get_client() is tcp_client.return_value

    tcp_client.assert_called_once_with(host="192.0.2.42", port=1502, timeout=3.0)


def test_get_client_creates_serial_client(hass):
    """Serial clients should be created with serial settings."""
    with patch("custom_components.kws306l.modbus.ModbusSerialClient", return_value=Mock()) as serial_client:
        client = KwsModbusClient(
            hass,
            KwsConnectionParams(protocol="serial", serial_port="/dev/ttyUSB2", slave_id=2),
        )
        assert client._get_client() is serial_client.return_value

    serial_client.assert_called_once_with(
        port="/dev/ttyUSB2",
        baudrate=9600,
        timeout=3.0,
        parity="N",
        stopbits=1,
        bytesize=8,
    )


def test_get_client_rejects_unsupported_protocol(hass):
    """Unsupported protocols should fail explicitly."""
    client = KwsModbusClient(hass, KwsConnectionParams(protocol="udp", slave_id=1))
    with pytest.raises(KwsModbusError):
        client._get_client()


def test_ensure_connected_raises_for_failed_connect(hass):
    """Failed connections should raise a domain-specific error."""
    fake = Mock()
    fake.connect.return_value = False
    client = KwsModbusClient(hass, KwsConnectionParams(protocol="tcp", host="192.0.2.43", slave_id=1))
    client._get_client = Mock(return_value=fake)
    client._close_sync = Mock()

    with pytest.raises(KwsModbusError):
        client._ensure_connected()

    client._close_sync.assert_called_once()


def test_read_registers_falls_back_to_unit_kwarg(hass):
    """The transport should support legacy pymodbus keyword arguments."""
    fake = Mock()
    fake.read_holding_registers.side_effect = [
        TypeError("unsupported keyword"),
        TypeError("unsupported keyword"),
        "fallback-result",
    ]
    client = KwsModbusClient(hass, KwsConnectionParams(protocol="tcp", host="192.0.2.44", slave_id=9))

    result = client._read_registers(fake, 14, 1)

    assert result == "fallback-result"
    assert fake.read_holding_registers.call_args_list[0].kwargs == {
        "address": 14,
        "count": 1,
        "device_id": 9,
    }
    assert fake.read_holding_registers.call_args_list[1].kwargs == {
        "address": 14,
        "count": 1,
        "slave": 9,
    }
    assert fake.read_holding_registers.call_args_list[2].kwargs == {
        "address": 14,
        "count": 1,
        "unit": 9,
    }


def test_read_blocks_sync_wraps_unexpected_errors(hass):
    """Unexpected exceptions should be wrapped as KwsModbusError."""
    client = KwsModbusClient(hass, KwsConnectionParams(protocol="tcp", host="192.0.2.45", slave_id=1))
    client._ensure_connected = Mock(return_value=Mock())
    client._read_registers = Mock(side_effect=RuntimeError("boom"))
    client._close_sync = Mock()

    with pytest.raises(KwsModbusError, match="boom"):
        client._read_blocks_sync((SimpleNamespace(start=14, count=1),))

    client._close_sync.assert_called_once()


def test_close_sync_clears_existing_client(hass):
    """Closing should dispose of the cached client."""
    fake = Mock()
    client = KwsModbusClient(hass, KwsConnectionParams(protocol="tcp", host="192.0.2.46", slave_id=1))
    client._client = fake

    client._close_sync()

    fake.close.assert_called_once()
    assert client._client is None
