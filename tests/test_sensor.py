"""Tests for the KWS306L sensor platform."""

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


async def test_sensor_entities_are_created_and_decoded(hass):
    """The integration should expose decoded sensor values."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Meter",
        data={
            CONF_PROTOCOL: PROTOCOL_TCP,
            CONF_HOST: "192.0.2.20",
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

    assert hass.states.get("sensor.meter_phase_a_voltage").state == "220.0"
    assert hass.states.get("sensor.meter_phase_a_current").state == "5.0"
    assert hass.states.get("sensor.meter_total_active_power").state == "123.4"
    assert hass.states.get("sensor.meter_total_reactive_power").state == "45.6"
    assert hass.states.get("sensor.meter_total_apparent_power").state == "78.9"
    assert hass.states.get("sensor.meter_total_power_factor").state == "0.995"
    assert hass.states.get("sensor.meter_frequency").state == "50.0"
    assert hass.states.get("sensor.meter_total_energy").state == "123.45"
    assert hass.states.get("sensor.meter_runtime").state == "120"
    assert hass.states.get("sensor.meter_meter_status").state == "on"

    alarm_state = hass.states.get("sensor.meter_alarm_mask")
    assert alarm_state.state == "33"
    assert alarm_state.attributes["active_alarms"] == ["overvoltage", "overtemperature"]
    assert alarm_state.attributes["bits"]["overtemperature"] is True

