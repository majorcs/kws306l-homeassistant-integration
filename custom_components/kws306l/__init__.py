"""The KWS306L integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import Kws306lDataUpdateCoordinator
from .modbus import KwsConnectionParams, KwsModbusClient


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the KWS306L integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up KWS306L from a config entry."""
    client = KwsModbusClient(hass, KwsConnectionParams.from_mapping(entry.data))
    coordinator = Kws306lDataUpdateCoordinator(hass, entry, client)

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        await client.async_close()
        raise

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    runtime = hass.data[DOMAIN].pop(entry.entry_id)
    client: KwsModbusClient = runtime["client"]
    await client.async_close()
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
