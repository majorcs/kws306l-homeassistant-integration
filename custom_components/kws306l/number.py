"""Number platform for writable KWS306L configuration registers."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import Kws306lCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class KwsNumberDescription(NumberEntityDescription):
    """Description for a writable KWS306L number entity."""

    register: int
    register_count: int = 1
    scale: int = 1


def _decode_registers(data: dict[int, int], address: int, register_count: int, scale: int) -> float | None:
    if address not in data:
        return None

    if register_count == 1:
        raw = int(data[address])
    else:
        if address + 1 not in data:
            return None
        raw = (int(data[address]) << 16) | int(data[address + 1])

    return raw / scale


def _encode_registers(value: float, register_count: int, scale: int) -> list[int]:
    raw = int(round(value * scale))
    if register_count == 1:
        return [raw]
    return [(raw >> 16) & 0xFFFF, raw & 0xFFFF]


NUMBER_DESCRIPTIONS: tuple[KwsNumberDescription, ...] = (
    KwsNumberDescription(
        key="overvoltage_limit",
        name="Overvoltage limit",
        register=64,
        native_min_value=0,
        native_max_value=290.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:flash-alert-outline",
        scale=10,
    ),
    KwsNumberDescription(
        key="undervoltage_limit",
        name="Undervoltage limit",
        register=65,
        native_min_value=0,
        native_max_value=220.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:flash-outline",
        scale=10,
    ),
    KwsNumberDescription(
        key="overcurrent_limit",
        name="Overcurrent limit",
        register=66,
        native_min_value=0,
        native_max_value=99.0,
        native_step=0.01,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:current-ac",
        scale=100,
    ),
    KwsNumberDescription(
        key="overpower_limit",
        name="Overpower limit",
        register=67,
        native_min_value=0,
        native_max_value=23.2,
        native_step=0.01,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:lightning-bolt-outline",
        scale=100,
    ),
    KwsNumberDescription(
        key="voltage_imbalance_limit",
        name="Voltage imbalance limit",
        register=68,
        native_min_value=0,
        native_max_value=290.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:sine-wave",
        scale=10,
    ),
    KwsNumberDescription(
        key="current_imbalance_limit",
        name="Current imbalance limit",
        register=69,
        native_min_value=0,
        native_max_value=99.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:current-dc",
        scale=10,
    ),
    KwsNumberDescription(
        key="countdown_minutes",
        name="Countdown",
        register=70,
        native_min_value=0,
        native_max_value=59999,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:timer-edit-outline",
    ),
    KwsNumberDescription(
        key="screensaver_minutes",
        name="Screensaver",
        register=71,
        native_min_value=0,
        native_max_value=59,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:monitor-dashboard",
    ),
    KwsNumberDescription(
        key="overtemperature_limit",
        name="Overtemperature limit",
        register=72,
        native_min_value=0,
        native_max_value=150,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:thermometer-alert",
    ),
    KwsNumberDescription(
        key="overelectricity_limit",
        name="Overelectricity limit",
        register=73,
        register_count=2,
        native_min_value=0,
        native_max_value=9_999_999,
        native_step=1,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:transmission-tower-export",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up writable KWS306L number entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(Kws306lNumber(coordinator, description) for description in NUMBER_DESCRIPTIONS)


class Kws306lNumber(Kws306lCoordinatorEntity, NumberEntity):
    """Representation of a writable KWS306L configuration register."""

    entity_description: KwsNumberDescription

    def __init__(self, coordinator, description: KwsNumberDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_unique_id}_number_{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the current register value."""
        return _decode_registers(
            self.coordinator.data,
            self.entity_description.register,
            self.entity_description.register_count,
            self.entity_description.scale,
        )

    async def async_set_native_value(self, value: float) -> None:
        """Write the provided register value to the device."""
        raw_values = _encode_registers(
            value,
            self.entity_description.register_count,
            self.entity_description.scale,
        )

        scaled_value = raw_values[0] / self.entity_description.scale
        if self.entity_description.register_count == 2:
            scaled_value = (
                ((raw_values[0] << 16) | raw_values[1]) / self.entity_description.scale
            )

        if scaled_value != value:
            raise HomeAssistantError("Only supported step values may be written")

        try:
            await self.coordinator.async_write_registers(
                self.entity_description.register,
                raw_values,
                refresh_count=self.entity_description.register_count,
            )
        except Exception as err:
            raise HomeAssistantError(str(err)) from err
