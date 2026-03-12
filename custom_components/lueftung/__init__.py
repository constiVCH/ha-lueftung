"""Lüftungssteuerung SEC Smart."""
from __future__ import annotations
import logging
from datetime import timedelta, time

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN, API_BASE_URL,
    CONF_DEVICE_ID, CONF_API_TOKEN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL,
    STORAGE_KEY, STORAGE_VERSION,
    CONF_TEMP_RULES, CONF_HUMIDITY_RULES, CONF_NIGHT_MODE,
    RULE_SENSOR, RULE_AREAS, RULE_THRESHOLD, RULE_CONDITION, RULE_MODE, RULE_ENABLED,
    NIGHT_START, NIGHT_END, NIGHT_AREAS, NIGHT_MODE, NIGHT_ENABLED,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    device_id = entry.data[CONF_DEVICE_ID]
    api_token = entry.data[CONF_API_TOKEN]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = LueftungCoordinator(hass, device_id, api_token, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    rules_data = await store.async_load() or {
        CONF_TEMP_RULES: [],
        CONF_HUMIDITY_RULES: [],
        CONF_NIGHT_MODE: {
            NIGHT_ENABLED: False,
            NIGHT_START: "22:00",
            NIGHT_END: "07:00",
            NIGHT_AREAS: [],
            NIGHT_MODE: "Manual 1",
        },
    }

    engine = LueftungAutomationEngine(hass, coordinator, store, rules_data)
    await engine.async_start()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "engine": engine,
        "store": store,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Panel registrieren
    from .panel import async_setup_panel
    await async_setup_panel(hass)

    # Service registrieren
    async def handle_save_rules(call):
        await engine.async_update_rules(dict(call.data))

    hass.services.async_register(DOMAIN, "save_rules", handle_save_rules)

    # Service: aktuelle Regeln als HA State speichern damit UI sie lesen kann
    async def handle_get_rules(call):
        hass.states.async_set(f"{DOMAIN}.rules_state", "ok", engine.rules)

    hass.services.async_register(DOMAIN, "get_rules", handle_get_rules)
    # Initial State setzen
    hass.states.async_set(f"{DOMAIN}.rules_state", "ok", engine.rules)

    # Verfügbare Sensoren als HA State publizieren (wird von der UI gelesen)
    async def _publish_sensors():
        temp = []
        humidity = []
        for state in hass.states.async_all():
            dc = state.attributes.get("device_class")
            name = state.attributes.get("friendly_name") or state.entity_id
            unit = state.attributes.get("unit_of_measurement") or ""
            entry = {"id": state.entity_id, "name": name, "state": state.state, "unit": unit}
            if dc == "temperature":
                temp.append(entry)
            elif dc == "humidity":
                humidity.append(entry)
        hass.states.async_set(f"{DOMAIN}.available_sensors", "ok", {
            "temperature": sorted(temp, key=lambda x: x["name"]),
            "humidity": sorted(humidity, key=lambda x: x["name"]),
        })

    await _publish_sensors()

    # Sensoren alle 5 Minuten aktualisieren
    async_track_time_interval(hass, lambda _: hass.async_create_task(_publish_sensors()), timedelta(minutes=5))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id)
    data["engine"].stop()
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
                    async with session.put(self._put_url, headers=self._headers, json={"areaid": area_id, "mode": mode}) as resp:
                        if resp.status not in (200, 204):
                            _LOGGER.error("API SET Fehler HTTP %s Area %s Mode %s", resp.status, area_id, mode)
                            return False
                        return True
        except aiohttp.ClientError as err:
            _LOGGER.error("Verbindungsfehler: %s", err)
            return False


class LueftungAutomationEngine:
    def __init__(self, hass, coordinator, store, rules):
        self.hass = hass
        self.coordinator = coordinator
        self.store = store
        self.rules = rules
        self._unsub = []
        self._unsub_timer = None

    async def async_start(self):
        self._setup_listeners()

    def stop(self):
        for u in self._unsub:
            u()
        if self._unsub_timer:
            self._unsub_timer()

    async def async_update_rules(self, new_rules: dict):
        self.rules = new_rules
        await self.store.async_save(new_rules)
        self.hass.states.async_set(f"{DOMAIN}.rules_state", "ok", self.rules)
        for u in self._unsub:
            u()
        self._unsub = []
        if self._unsub_timer:
            self._unsub_timer()
        self._setup_listeners()
        _LOGGER.info("Lüftungsregeln gespeichert")

    def _setup_listeners(self):
        sensors = set()
        for rule in self.rules.get(CONF_TEMP_RULES, []) + self.rules.get(CONF_HUMIDITY_RULES, []):
            if rule.get(RULE_ENABLED) and rule.get(RULE_SENSOR):
                sensors.add(rule[RULE_SENSOR])
        if sensors:
            @callback
            def on_change(event):
                self.hass.async_create_task(self._evaluate_rules())
            self._unsub.append(async_track_state_change_event(self.hass, list(sensors), on_change))

        @callback
        def on_tick(now):
            self.hass.async_create_task(self._evaluate_night())
        self._unsub_timer = async_track_time_interval(self.hass, on_tick, timedelta(minutes=1))

    async def _evaluate_rules(self):
        for rule_key in (CONF_TEMP_RULES, CONF_HUMIDITY_RULES):
            for rule in self.rules.get(rule_key, []):
                if not rule.get(RULE_ENABLED):
                    continue
                sensor_id = rule.get(RULE_SENSOR)
                if not sensor_id:
                    continue
                state = self.hass.states.get(sensor_id)
                if not state or state.state in ("unknown", "unavailable", ""):
                    continue
                try:
                    value = float(state.state)
                    threshold = float(rule.get(RULE_THRESHOLD, 0))
                except (ValueError, TypeError):
                    continue
                condition = rule.get(RULE_CONDITION, "above")
                triggered = (condition == "above" and value > threshold) or (condition == "below" and value < threshold)
                if triggered:
                    mode = rule.get(RULE_MODE, "Manual 1")
                    for area_id in rule.get(RULE_AREAS, []):
                        await self.coordinator.async_set_area_mode(int(area_id), mode)

    async def _evaluate_night(self):
        night = self.rules.get(CONF_NIGHT_MODE, {})
        if not night.get(NIGHT_ENABLED):
            return
        try:
            start = time.fromisoformat(night.get(NIGHT_START, "22:00"))
            end = time.fromisoformat(night.get(NIGHT_END, "07:00"))
        except ValueError:
            return
        now = dt_util.now().time()
        is_night = (now >= start or now < end) if start > end else (start <= now < end)
        if is_night:
            mode = night.get(NIGHT_MODE, "Manual 1")
            for area_id in night.get(NIGHT_AREAS, []):
                await self.coordinator.async_set_area_mode(int(area_id), mode)
