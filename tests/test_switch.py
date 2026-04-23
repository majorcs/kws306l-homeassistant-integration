"""Tests for writable KWS306L switch entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kws306l.const import (
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DOMAIN,
    PROTOCOL_TCP,
)


def _sample_registers() -> dict[int, int]:
    values = {12: 0x0203}
    values.update({address: 0 for address in range(14, 75)})
    values[63] = 1
    return values


async def test_switch_entity_tracks_meter_status(hass):
    """The meter status should be exposed as a switch entity."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Meter",
        data={
            CONF_PROTOCOL: PROTOCOL_TCP,
            CONF_HOST: "192.0.2.33",
            CONF_PORT: DEFAULT_PORT,
            CONF_SLAVE_ID: 3,
            CONF_SCAN_INTERVAL: 30,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.kws306l.modbus.KwsModbusClient.async_read_blocks",
        new=AsyncMock(return_value=_sample_registers()),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("switch.meter_meter_output")
    assert state is not None
    assert state.state == "on"
    assert hass.states.get("sensor.meter_meter_status") is None


async def test_switch_entity_writes_meter_status(hass):
    """Turning the switch off should write register 63."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Meter",
        data={
            CONF_PROTOCOL: PROTOCOL_TCP,
            CONF_HOST: "192.0.2.34",
            CONF_PORT: DEFAULT_PORT,
            CONF_SLAVE_ID: 3,
            CONF_SCAN_INTERVAL: 30,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.kws306l.modbus.KwsModbusClient.async_read_blocks",
        new=AsyncMock(return_value=_sample_registers()),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async def _write_side_effect(address: int, value: int) -> None:
        updated = dict(coordinator.data)
        updated[address] = value
        coordinator.async_set_updated_data(updated)

    coordinator.async_write_register = AsyncMock(side_effect=_write_side_effect)

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.meter_meter_output"},
        blocking=True,
    )
    await hass.async_block_till_done()

    coordinator.async_write_register.assert_awaited_once_with(63, 0)
    assert hass.states.get("switch.meter_meter_output").state == "off"