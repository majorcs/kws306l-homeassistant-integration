"""Switch platform for writable KWS306L binary controls."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import Kws306lCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up writable KWS306L switch entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([Kws306lMeterStatusSwitch(coordinator)])


class Kws306lMeterStatusSwitch(Kws306lCoordinatorEntity, SwitchEntity):
    """Representation of the KWS306L output state."""

    _attr_name = "Meter output"
    _attr_icon = "mdi:power"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_unique_id}_switch_meter_status"

    @property
    def is_on(self) -> bool | None:
        """Return whether the meter output is enabled."""
        value = self.coordinator.data.get(63)
        return None if value is None else int(value) == 1

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the meter output on."""
        await self._async_set_output(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the meter output off."""
        await self._async_set_output(False)

    async def _async_set_output(self, enabled: bool) -> None:
        try:
            await self.coordinator.async_write_register(63, 1 if enabled else 0)
        except Exception as err:
            raise HomeAssistantError(str(err)) from err