"""Config Flow für Lüftungssteuerung."""
from __future__ import annotations
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, API_BASE_URL, CONF_DEVICE_ID, CONF_API_TOKEN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_DEVICE_ID): str,
    vol.Required(CONF_API_TOKEN): str,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(int, vol.Range(min=30, max=3600)),
})


async def _validate_api(device_id: str, api_token: str) -> str | None:
    url = f"{API_BASE_URL}/devices/{device_id}/areas"
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    try:
        async with async_timeout.timeout(10):
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        return "invalid_auth"
                    if resp.status != 200:
                        return "cannot_connect"
                    return None
    except Exception:
        return "cannot_connect"


class LueftungConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID].strip().upper()
            api_token = user_input[CONF_API_TOKEN].strip()
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()
            error = await _validate_api(device_id, api_token)
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title=f"Lüftung {device_id}",
                    data={
                        CONF_DEVICE_ID: device_id,
                        CONF_API_TOKEN: api_token,
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    },
                )
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)
