"""Shared entity helpers for KWS306L."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import Kws306lDataUpdateCoordinator


class Kws306lCoordinatorEntity(CoordinatorEntity[Kws306lDataUpdateCoordinator]):
    """Base entity class for coordinator-backed KWS306L entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: Kws306lDataUpdateCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the shared device metadata for all entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device_unique_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=self.coordinator.entry.title,
        )

