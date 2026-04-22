"""Data update coordinator for KWS306L."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, DOMAIN, build_unique_id
from .modbus import KwsModbusClient, KwsModbusError
from .register_map import READ_BLOCKS

_LOGGER = logging.getLogger(__name__)


class Kws306lDataUpdateCoordinator(DataUpdateCoordinator[dict[int, int]]):
    """Fetch data from a KWS306L meter."""

    def __init__(self, hass, entry: ConfigEntry, client: KwsModbusClient) -> None:
        self.entry = entry
        self.client = client
        self.device_unique_id = build_unique_id(entry.data)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.device_unique_id}",
            update_interval=timedelta(seconds=int(entry.options.get(CONF_SCAN_INTERVAL, entry.data[CONF_SCAN_INTERVAL]))),
        )

    async def _async_update_data(self) -> dict[int, int]:
        try:
            return await self.client.async_read_blocks(READ_BLOCKS)
        except KwsModbusError as err:
            raise UpdateFailed(str(err)) from err

