"""Lüftungssteuerung SEC Smart."""
from __future__ import annotations
import logging
from datetime import timedelta

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, API_BASE_URL, CONF_DEVICE_ID, CONF_API_TOKEN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    device_id = entry.data[CONF_DEVICE_ID]
    api_token = entry.data[CONF_API_TOKEN]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = LueftungCoordinator(hass, device_id, api_token, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Service: Modus für einen Bereich setzen – nutzbar in HA-Automationen
    async def handle_set_mode(call):
        area_id = int(call.data.get("area_id", 1))
        mode = call.data.get("mode", "Fans off")
        await coordinator.async_set_area_mode(area_id, mode)

    hass.services.async_register(DOMAIN, "set_mode", handle_set_mode)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[DOMAIN].pop(entry.entry_id)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


class LueftungCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, device_id, api_token, scan_interval):
        super().__init__(hass, _LOGGER, name=f"Lüftung {device_id}", update_interval=timedelta(seconds=scan_interval))
        self.device_id = device_id
        self._base_url = f"{API_BASE_URL}/devices/{device_id}/areas"
        self._headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
        self._put_url = f"{API_BASE_URL}/devices/{device_id}/areas/mode"

    async def _async_update_data(self) -> dict:
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(self._base_url, headers=self._headers) as resp:
                        if resp.status == 401:
                            raise UpdateFailed("API Token ungültig (401)")
                        if resp.status != 200:
                            raise UpdateFailed(f"API Fehler: HTTP {resp.status}")
                        return await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Verbindungsfehler: {err}") from err

    async def async_set_area_mode(self, area_id: int, mode: str) -> bool:
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.put(self._put_url, headers=self._headers,
                                           json={"areaid": area_id, "mode": mode}) as resp:
                        if resp.status not in (200, 204):
                            _LOGGER.error("API Fehler HTTP %s Area %s Mode %s", resp.status, area_id, mode)
                            return False
                        return True
        except aiohttp.ClientError as err:
            _LOGGER.error("Verbindungsfehler: %s", err)
            return False
