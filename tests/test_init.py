"""Tests for integration setup and unload helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.config_entries import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kws306l import async_reload_entry, async_setup, async_setup_entry, async_unload_entry
from custom_components.kws306l.const import (
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_PORT,
    CONF_SLAVE_ID,
    DOMAIN,
    PROTOCOL_SERIAL,
)


async def test_async_setup_initializes_domain_data(hass):
    """The domain storage should be prepared during setup."""
    assert await async_setup(hass, {})
    assert DOMAIN in hass.data


async def test_async_setup_entry_closes_client_when_first_refresh_fails(hass):
    """Failed first refreshes should close the client before re-raising."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Meter",
        data={
            CONF_PROTOCOL: PROTOCOL_SERIAL,
            CONF_SERIAL_PORT: "/dev/ttyUSB0",
            CONF_SLAVE_ID: 1,
            CONF_SCAN_INTERVAL: 30,
        },
    )
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})

    with (
        patch("custom_components.kws306l.KwsModbusClient") as client_cls,
        patch("custom_components.kws306l.Kws306lDataUpdateCoordinator") as coordinator_cls,
    ):
        client = client_cls.return_value
        client.async_close = AsyncMock()
        coordinator = coordinator_cls.return_value
        coordinator.async_config_entry_first_refresh = AsyncMock(side_effect=ConfigEntryNotReady)

        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)

    client.async_close.assert_awaited_once()


async def test_async_unload_entry_returns_false_when_platform_unload_fails(hass):
    """Unload should stop when Home Assistant fails to unload platforms."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_PROTOCOL: PROTOCOL_SERIAL,
            CONF_SERIAL_PORT: "/dev/ttyUSB0",
            CONF_SLAVE_ID: 1,
            CONF_SCAN_INTERVAL: 30,
        },
    )
    hass.data.setdefault(DOMAIN, {})

    with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=False)):
        assert not await async_unload_entry(hass, entry)


async def test_async_reload_entry_delegates_to_home_assistant(hass):
    """Reload helper should forward to the config entries manager."""
    entry = MockConfigEntry(domain=DOMAIN)
    with patch.object(hass.config_entries, "async_reload", AsyncMock()) as reload_mock:
        await async_reload_entry(hass, entry)

    reload_mock.assert_awaited_once_with(entry.entry_id)

