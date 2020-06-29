"""
Home Assistant integration with the Meraki Scanning API

For more details about this integration, please refer to
https://github.com/custom-components/blueprint
"""
import asyncio
import logging
from datetime import timedelta

from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .http import MerakiView
from .const import (
    API_V2,
    CONF_SECRET,
    CONF_API_VERSION,
    CONF_VALIDATOR,
    DOMAIN,
    PLATFORMS,
)

PLATFORMS = ["device_tracker"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integratfion using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry):
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})

    hass.http.register_view(MerakiView(hass, config))

    # Ensure the device_tracker gets configured
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config, DEVICE_TRACKER)
    )
    return True
