"""Tests for the KWS306L data coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kws306l.const import (
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DOMAIN,
    PROTOCOL_TCP,
)
from custom_components.kws306l.coordinator import Kws306lDataUpdateCoordinator
from custom_components.kws306l.modbus import KwsModbusError


def _entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Meter",
        data={
            CONF_PROTOCOL: PROTOCOL_TCP,
            CONF_HOST: "192.0.2.40",
            CONF_PORT: DEFAULT_PORT,
            CONF_SLAVE_ID: 3,
            CONF_SCAN_INTERVAL: 30,
        },
    )


async def test_async_update_data_wraps_modbus_error(hass):
    """Coordinator refresh failures should be surfaced as UpdateFailed."""
    client = Mock()
    client.async_read_blocks = AsyncMock(side_effect=KwsModbusError("boom"))

    coordinator = Kws306lDataUpdateCoordinator(hass, _entry(), client)

    with pytest.raises(UpdateFailed, match="boom"):
        await coordinator._async_update_data()


async def test_async_write_register_updates_cached_data(hass):
    """Single-register writes should update the cached coordinator data."""
    client = Mock()
    client.async_write_registers = AsyncMock()
    client.async_read_blocks = AsyncMock(return_value={70: 45})

    coordinator = Kws306lDataUpdateCoordinator(hass, _entry(), client)
    coordinator.async_set_updated_data({70: 30})

    await coordinator.async_write_register(70, 45)

    client.async_write_registers.assert_awaited_once_with(70, [45])
    client.async_read_blocks.assert_awaited_once()
    assert coordinator.data[70] == 45


async def test_async_write_registers_updates_multiple_cached_values(hass):
    """Multi-register writes should refresh all returned register values."""
    client = Mock()
    client.async_write_registers = AsyncMock()
    client.async_read_blocks = AsyncMock(return_value={73: 1, 74: 4464})

    coordinator = Kws306lDataUpdateCoordinator(hass, _entry(), client)
    coordinator.async_set_updated_data({73: 0, 74: 250})

    await coordinator.async_write_registers(73, [1, 4464], refresh_count=2)

    client.async_write_registers.assert_awaited_once_with(73, [1, 4464])
    client.async_read_blocks.assert_awaited_once()
    assert coordinator.data[73] == 1
    assert coordinator.data[74] == 4464