"""Support for the Meraki CMX location service."""
import json
import logging

from homeassistant.components.device_tracker import SOURCE_TYPE_ROUTER
from homeassistant.components.device_tracker.config_entry import TrackerEntity

from homeassistant.core import callback
from homeassistant.helpers import device_registry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN, OBSERVATION_EVENT


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up an endpoint for the Meraki tracker."""

    @callback
    def _receive_data(event):
        _LOGGER.debug("Received data %s" % event)
        return async_add_entities([MerakiScanningEntity(event["mac"], event["gps"])])

    # hass.data[DOMAIN]["_receive_data"][
    #     config_entry.entry_id
    # ] =
    async_dispatcher_connect(hass, OBSERVATION_EVENT, _receive_data)

    return True


class MerakiScanningEntity(TrackerEntity, RestoreEntity):
    """Represents a tracked device"""

    def __init__(self, name, gps):
        self._name = name
        self._gps = gps

    @property
    def name(self):
        return self._name

    @property
    def latitude(self):
        return self._gps[0]

    @property
    def longitude(self):
        return self._gps[1]

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self._name

    async def async_added_to_hass(self):
        """Register state update callback."""
        await super().async_added_to_hass()
        self._unsub_dispatcher = async_dispatcher_connect(
            self.hass, OBSERVATION_EVENT, self._async_receive_data
        )

        # if self._attributes:
        #     return

        # state = await self.async_get_last_state()

        # if state is None:
        #     self._gps = (None, None)
        #     return

        # attr = state.attributes
        # self._gps = (attr.get(ATTR_LATITUDE), attr.get(ATTR_LONGITUDE))

    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        await super().async_will_remove_from_hass()
        self._unsub_dispatcher()
        self.hass.data[DOMAIN]["devices"].remove(self._unique_id)

    @callback
    def _async_receive_data(self, event):
        """Mark the device as seen."""
        if event["mac"] != self._name:
            return

        # self._attributes.update(attributes)
        # self._location_name = location_name
        self._gps = event["gps"]
        self.async_write_ha_state()
