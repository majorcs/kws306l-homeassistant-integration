"""Tests for writable KWS306L number entities."""

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
    values.update(
        {
            14: 22000,
            15: 22100,
            16: 22200,
            17: 0,
            18: 5000,
            19: 0,
            20: 6000,
            21: 0,
            22: 7000,
            23: 0,
            24: 1234,
            31: 0,
            32: 456,
            39: 0,
            40: 789,
            47: 995,
            48: 996,
            49: 997,
            50: 998,
            51: 5000,
            52: 0,
            53: 12345,
            54: 0,
            55: 2000,
            56: 0,
            57: 3000,
            58: 0,
            59: 4000,
            60: 25,
            61: 120,
            62: 0b0010_0001,
            63: 1,
            64: 2750,
            65: 850,
            66: 8000,
            67: 1800,
            68: 50,
            69: 15,
            70: 30,
            71: 10,
            72: 150,
            73: 0,
            74: 250,
        }
    )
    return values


async def test_number_entities_are_created_with_live_values(hass):
    """Editable configuration registers should be exposed as number entities."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Meter",
        data={
            CONF_PROTOCOL: PROTOCOL_TCP,
            CONF_HOST: "192.0.2.30",
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

    countdown = hass.states.get("number.meter_countdown")
    overvoltage = hass.states.get("number.meter_overvoltage_limit")
    overpower = hass.states.get("number.meter_overpower_limit")
    screensaver = hass.states.get("number.meter_screensaver")
    overelectricity = hass.states.get("number.meter_overelectricity_limit")

    assert countdown is not None
    assert countdown.state == "30.0"
    assert countdown.attributes["unit_of_measurement"] == "min"
    assert hass.states.get("sensor.meter_countdown") is None

    assert overvoltage is not None
    assert overvoltage.state == "275.0"
    assert overvoltage.attributes["unit_of_measurement"] == "V"
    assert hass.states.get("sensor.meter_overvoltage_limit") is None

    assert overpower is not None
    assert overpower.state == "18.0"
    assert overpower.attributes["unit_of_measurement"] == "kW"
    assert hass.states.get("sensor.meter_overpower_limit") is None

    assert screensaver is not None
    assert screensaver.state == "10.0"
    assert screensaver.attributes["unit_of_measurement"] == "min"
    assert hass.states.get("sensor.meter_screensaver") is None

    assert overelectricity is not None
    assert overelectricity.state == "250.0"
    assert overelectricity.attributes["unit_of_measurement"] == "kWh"
    assert hass.states.get("sensor.meter_overelectricity_limit") is None


async def test_number_entities_write_through_the_coordinator(hass):
    """Setting a number entity should write the register and update state."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Meter",
        data={
            CONF_PROTOCOL: PROTOCOL_TCP,
            CONF_HOST: "192.0.2.31",
            CONF_PORT: DEFAULT_PORT,
            CONF_SLAVE_ID: 3,
            CONF_SCAN_INTERVAL: 30,
        },
    )
    entry.add_to_hass(hass)

    registers = _sample_registers()

    with patch(
        "custom_components.kws306l.modbus.KwsModbusClient.async_read_blocks",
        new=AsyncMock(return_value=registers),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async def _write_side_effect(address: int, values: list[int], *, refresh_count: int | None = None) -> None:
        updated = dict(coordinator.data)
        for offset, register in enumerate(values):
            updated[address + offset] = register
        coordinator.async_set_updated_data(updated)

    coordinator.async_write_registers = AsyncMock(side_effect=_write_side_effect)

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.meter_overvoltage_limit", "value": 280.5},
        blocking=True,
    )
    await hass.async_block_till_done()

    coordinator.async_write_registers.assert_awaited_once_with(64, [2805], refresh_count=1)
    assert hass.states.get("number.meter_overvoltage_limit").state == "280.5"


async def test_overelectricity_number_writes_two_registers(hass):
    """Two-register writable values should be encoded high word first."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Meter",
        data={
            CONF_PROTOCOL: PROTOCOL_TCP,
            CONF_HOST: "192.0.2.32",
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

    async def _write_side_effect(address: int, values: list[int], *, refresh_count: int | None = None) -> None:
        updated = dict(coordinator.data)
        for offset, register in enumerate(values):
            updated[address + offset] = register
        coordinator.async_set_updated_data(updated)

    coordinator.async_write_registers = AsyncMock(side_effect=_write_side_effect)

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.meter_overelectricity_limit", "value": 70000},
        blocking=True,
    )
    await hass.async_block_till_done()

    coordinator.async_write_registers.assert_awaited_once_with(73, [1, 4464], refresh_count=2)
    assert hass.states.get("number.meter_overelectricity_limit").state == "70000.0"