"""Support for the Meraki CMX location service."""
import json
import logging

import voluptuous as vol

from homeassistant.components.device_tracker import PLATFORM_SCHEMA, SOURCE_TYPE_ROUTER
from homeassistant.components.http import HomeAssistantView
from homeassistant.const import (
    HTTP_BAD_REQUEST,
    HTTP_UNAUTHORIZED,
    HTTP_UNPROCESSABLE_ENTITY,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, Config, HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, CONF_VALIDATOR, CONF_SECRET, OBSERVATION_EVENT

_LOGGER = logging.getLogger(__name__)


class MerakiView(HomeAssistantView):
    """View to handle Meraki requests."""

    requires_auth = False
    url = "/api/%s" % DOMAIN
    name = "api:%s" % DOMAIN

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize Meraki URL endpoints."""
        self.hass = hass
        self.secret = entry.data[CONF_SECRET]
        self.validator = entry.data[CONF_VALIDATOR]

    def validate_secret(self, secret):
        """Validate shared secret."""
        if not secret:
            _LOGGER.error("no secret supplied")
            return False

        if secret != self.secret:
            _LOGGER.error("invalid secret supplied")
            _LOGGER.debug("received secret %s", secret)
            return False

        _LOGGER.debug("valid secret")
        return True

    async def get(self, request):
        """
        When Meraki makes a GET request to check the validator we land here.

        All we have to do is return the validator the user configured.
        """

        _LOGGER.debug("Received GET: %s" % request.path_qs)
        return self.validator

    async def post(self, request):
        """
        When Meraki POSTs updates with Observation data we land here.

        This method does the basic validation of the request and then
        farms it out towards a handler for the appropriate API version.
        """

        # ensure the payload is valid JSON
        try:
            data = await request.json()
        except ValueError:
            _LOGGER.debug("POST received with invalid JSON")
            return self.json_message("Invalid JSON", HTTP_BAD_REQUEST)
        _LOGGER.debug("Meraki Data from Post: %s", json.dumps(data))

        # authenticate the request
        if not self.validate_secret(data.get("secret", False)):
            return self.json_message("Invalid secret", HTTP_UNAUTHORIZED)

        # validate version + payload format
        handlers = {
            "2.0": {
                "callback": self._handle_2_0,
                "types": ["DevicesSeen", "BluetoothDevicesSeen"],
            },
            "3.0": {"callback": self._handle_3_0, "types": ["WiFi", "BLE"]},
        }
        handler = handlers.get(data["version"], None)

        if handler is None:
            _LOGGER.error("Invalid API version: %s", data["version"])
            return self.json_message("Invalid version", HTTP_UNPROCESSABLE_ENTITY)

        if data["type"] not in handler["types"]:
            _LOGGER.error("Unknown Device %s", data["type"])
            return self.json_message("Invalid device type", HTTP_UNPROCESSABLE_ENTITY)

        _LOGGER.debug(
            "Processing version=%s, type=%s" % (data["version"], data["type"])
        )

        # skip empty events
        if not data["data"]["observations"]:
            _LOGGER.debug("No observations found")
            return

        # process payload, TODO: make this async
        return handler["callback"](data["data"])

    def _fire_event(self, event):
        return async_dispatcher_send(self.hass, OBSERVATION_EVENT, event)

    @callback
    def _handle_3_0(self, data):
        for e in data["observations"]:
            event = {
                "mac": e["clientMac"],
                "gps": None,
                "attrs": {
                    "manufacturer": e["manufacturer"],
                    "os": e["os"],
                    "ssid": e["ssid"],
                    "ipv4": e["ipv4"],
                    "ipv6": e["ipv6"],
                },
            }

            if len(e["locations"]) > 0:
                loc = next(
                    l for l in e["locations"] if l["time"] == e["latestRecord"]["time"]
                )
                lat = loc["lat"]
                lng = loc["lng"]

                e["gps"] = (lat, lng)

            else:
                _LOGGER.debug("No location found for %s" % event["mac"])

            self._fire_event(event)

        return

    @callback
    def _handle_2_0(self, hass, data):

        for i in data["observations"]:

            lat = i["location"]["lat"]
            lng = i["location"]["lng"]
            try:
                accuracy = int(float(i["location"]["unc"]))
            except ValueError:
                accuracy = 0

            mac = i["clientMac"]
            _LOGGER.debug("clientMac: %s", mac)

            if lat == "NaN" or lng == "NaN":
                _LOGGER.debug("No coordinates received, skipping location for: %s", mac)
                gps_location = None
                accuracy = None
            else:
                gps_location = (lat, lng)

            # attrs = {}
            # if i.get("os", False):
            #     attrs["os"] = i["os"]
            # if i.get("manufacturer", False):
            #     attrs["manufacturer"] = i["manufacturer"]
            # if i.get("ipv4", False):
            #     attrs["ipv4"] = i["ipv4"]
            # if i.get("ipv6", False):
            #     attrs["ipv6"] = i["ipv6"]
            # if i.get("seenTime", False):
            #     attrs["seenTime"] = i["seenTime"]
            # if i.get("ssid", False):
            #     attrs["ssid"] = i["ssid"]
            # hass.async_create_task(
            #     self.async_see(
            #         gps=gps_location,
            #         mac=mac,
            #         source_type=SOURCE_TYPE_ROUTER,
            #         gps_accuracy=accuracy,
            #         attributes=attrs,
            #     )
            # )
