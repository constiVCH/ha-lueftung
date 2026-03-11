"""Registriert das Lüftungs-Panel in der HA-Sidebar."""
from __future__ import annotations
import os

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.frontend import async_register_built_in_panel


async def async_setup_panel(hass):
    panel_dir = os.path.dirname(__file__)
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                url_path="/lueftung_static",
                path=panel_dir,
                cache_headers=False,
            )
        ])
    except RuntimeError:
        pass  # Already registered

    try:
        async_register_built_in_panel(
            hass,
            component_name="iframe",
            sidebar_title="Lüftung",
            sidebar_icon="mdi:fan",
            frontend_url_path="lueftung-panel",
            config={"url": "/lueftung_static/lueftung_ui.html"},
            require_admin=False,
        )
    except ValueError:
        pass  # Already registered
