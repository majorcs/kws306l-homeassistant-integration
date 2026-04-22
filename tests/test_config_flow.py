"""Tests for the KWS306L config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kws306l.const import (
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_PORT,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DOMAIN,
    PROTOCOL_SERIAL,
    PROTOCOL_TCP,
)
from custom_components.kws306l.modbus import KwsModbusError


def _register_snapshot() -> dict[int, int]:
    snapshot = {12: 0x0203}
    snapshot.update({address: 0 for address in range(14, 75)})
    return snapshot


async def test_tcp_config_flow_creates_entry(hass):
    """TCP flow should create a config entry after a successful validation."""
    with (
        patch(
            "custom_components.kws306l.config_flow.KwsModbusClient.async_validate_connection",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "custom_components.kws306l.modbus.KwsModbusClient.async_read_blocks",
            new=AsyncMock(return_value=_register_snapshot()),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PROTOCOL: PROTOCOL_TCP},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "tcp"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.0.2.15",
                CONF_PORT: DEFAULT_PORT,
                CONF_SLAVE_ID: 3,
                CONF_SCAN_INTERVAL: 45,
                CONF_NAME: "Rack meter",
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Rack meter"
    assert result["data"] == {
        CONF_PROTOCOL: PROTOCOL_TCP,
        CONF_HOST: "192.0.2.15",
        CONF_PORT: DEFAULT_PORT,
        CONF_SLAVE_ID: 3,
        CONF_SCAN_INTERVAL: 45,
        CONF_NAME: "Rack meter",
    }


async def test_serial_config_flow_aborts_for_duplicate(hass):
    """The flow should reject duplicate serial devices."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{PROTOCOL_SERIAL}:/dev/ttyUSB0:1",
        data={
            CONF_PROTOCOL: PROTOCOL_SERIAL,
            CONF_SERIAL_PORT: "/dev/ttyUSB0",
            CONF_SLAVE_ID: 1,
            CONF_SCAN_INTERVAL: 30,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROTOCOL: PROTOCOL_SERIAL},
    )

    assert result["step_id"] == "serial"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SERIAL_PORT: "/dev/ttyUSB0",
            CONF_SLAVE_ID: 1,
            CONF_SCAN_INTERVAL: 30,
            CONF_NAME: "",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_updates_scan_interval(hass):
    """The options flow should store an updated scan interval."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Meter",
        data={
            CONF_PROTOCOL: PROTOCOL_TCP,
            CONF_HOST: "192.0.2.25",
            CONF_PORT: DEFAULT_PORT,
            CONF_SLAVE_ID: 2,
            CONF_SCAN_INTERVAL: 30,
        },
        options={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_SCAN_INTERVAL: 120},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_SCAN_INTERVAL: 120}


async def test_tcp_config_flow_shows_connection_error(hass):
    """TCP validation failures should keep the user on the form."""
    with patch(
        "custom_components.kws306l.config_flow.KwsModbusClient.async_validate_connection",
        new=AsyncMock(side_effect=KwsModbusError("cannot connect")),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PROTOCOL: PROTOCOL_TCP},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.0.2.16",
                CONF_PORT: DEFAULT_PORT,
                CONF_SLAVE_ID: 3,
                CONF_SCAN_INTERVAL: 30,
                CONF_NAME: "",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_serial_config_flow_shows_connection_error(hass):
    """Serial validation failures should keep the user on the form."""
    with patch(
        "custom_components.kws306l.config_flow.KwsModbusClient.async_validate_connection",
        new=AsyncMock(side_effect=KwsModbusError("cannot connect")),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PROTOCOL: PROTOCOL_SERIAL},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_SERIAL_PORT: "/dev/ttyUSB1",
                CONF_SLAVE_ID: 2,
                CONF_SCAN_INTERVAL: 30,
                CONF_NAME: "",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
