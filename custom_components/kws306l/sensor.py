"""Sensor platform for KWS306L."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import Kws306lCoordinatorEntity
from .register_map import ALARM_BITS, KwsSensorDescription, SENSOR_DESCRIPTIONS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KWS306L sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(Kws306lSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS)


class Kws306lSensor(Kws306lCoordinatorEntity, SensorEntity):
    """Representation of a KWS306L sensor."""

    entity_description: KwsSensorDescription

    def __init__(self, coordinator, description: KwsSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_unique_id}_{description.key}"

    @property
    def native_value(self) -> int | float | str | None:
        """Return the decoded sensor value."""
        return self.entity_description.decoder(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        """Return alarm details for the alarm mask register."""
        if self.entity_description.key != "alarm_mask":
            return None

        mask = int(self.native_value or 0)
        return {
            "active_alarms": [name for bit, name in ALARM_BITS.items() if mask & (1 << bit)],
            "bits": {name: bool(mask & (1 << bit)) for bit, name in ALARM_BITS.items()},
        }

