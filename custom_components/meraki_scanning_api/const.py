"""Meraki Scanning API component constants."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

NAME = "Meraki Scanning API"
DOMAIN = "meraki_scanning_api"
OBSERVATION_EVENT = "new_observation"

PLATFORMS = ["device_tracker"]

# Configuration and options
CONF_SECRET = "secret"
CONF_API_VERSION = "api_version"
CONF_VALIDATOR = "validator"

API_V2 = "2.0"


CONFIG_ENTRY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_VERSION, default=API_V2): vol.In([API_V2]),
        vol.Required(CONF_SECRET): str,
        vol.Required(CONF_VALIDATOR): str,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [CONFIG_ENTRY_SCHEMA]))}
)
