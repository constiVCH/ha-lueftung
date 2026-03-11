"""Select-Entitäten für jeden Lüftungsbereich."""
from __future__ import annotations
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LueftungCoordinator
from .const import DOMAIN, LUEFTUNG_MODES, NUM_AREAS, CONF_DEVICE_ID

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: LueftungCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    device_id = entry.data[CONF_DEVICE_ID]
    async_add_entities([LueftungAreaSelect(coordinator, device_id, i) for i in range(1, NUM_AREAS + 1)])


class LueftungAreaSelect(CoordinatorEntity, SelectEntity):
    _attr_options = LUEFTUNG_MODES
    _attr_icon = "mdi:fan"
    _attr_has_entity_name = True

    def __init__(self, coordinator: LueftungCoordinator, device_id: str, area_id: int):
        super().__init__(coordinator)
        self._area_id = area_id
        self._area_key = f"area{area_id}"
        self._attr_unique_id = f"lueftung_{device_id}_area{area_id}"
        self._attr_name = f"Bereich {area_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"Lüftungsanlage {device_id}",
            manufacturer="SEC Smart",
            model="Lüftungssteuerung",
        )

    @property
    def current_option(self) -> str | None:
        if not self.coordinator.data:
            return None
        mode = self.coordinator.data.get(self._area_key, {}).get("mode")
        return mode if mode in LUEFTUNG_MODES else None

    async def async_select_option(self, option: str) -> None:
        success = await self.coordinator.async_set_area_mode(self._area_id, option)
        if success:
            if self.coordinator.data:
                self.coordinator.data.setdefault(self._area_key, {})["mode"] = option
                self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
