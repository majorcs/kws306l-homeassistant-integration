"""Data update coordinator for KWS306L."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, DOMAIN, build_unique_id
from .modbus import KwsModbusClient, KwsModbusError
from .register_map import READ_BLOCKS, RegisterBlock

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

    async def async_write_registers(
        self,
        address: int,
        values: list[int],
        *,
        refresh_count: int | None = None,
    ) -> None:
        """Write one or more registers and refresh the cached state for them."""
        await self.client.async_write_registers(address, values)

        refreshed = await self.client.async_read_blocks(
            (RegisterBlock(start=address, count=refresh_count or len(values)),)
        )

        updated_data = dict(self.data)
        updated_data.update(refreshed)
        self.async_set_updated_data(updated_data)

    async def async_write_register(self, address: int, value: int) -> None:
        """Write a single register and refresh the cached state for it."""
        await self.async_write_registers(address, [value], refresh_count=1)

