"""Support for iCal-URLs."""

import copy
import logging

from homeassistant.components.calendar import (
    ENTITY_ID_FORMAT,
    CalendarEventDevice,
    calculate_offset,
    is_offset_reached,
)
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import generate_entity_id

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
OFFSET = "!!"


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the iCal Calendar platform."""
    config = config_entry.data
    _LOGGER.debug("Running setup_platform for calendar")
    _LOGGER.debug(f"Conf: {config}")
    name = config.get(CONF_NAME)

    entity_id = generate_entity_id(ENTITY_ID_FORMAT, DOMAIN + " " + name, hass=hass)

    ical_events = hass.data[DOMAIN][name]

    calendar = ICalCalendarEventDevice(hass, name, entity_id, ical_events)

    async_add_entities([calendar], True)


class ICalCalendarEventDevice(CalendarEventDevice):
    """A device for getting the next Task from a WebDav Calendar."""

    def __init__(self, hass, name, entity_id, ical_events):
        """Create the iCal Calendar Event Device."""
        self.entity_id = entity_id
        self._event = None
        self._name = name
        self._offset_reached = False
        self._is_free = False
        self.ical_events = ical_events

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        return {
            "offset_reached": self._offset_reached,
            "is_free": self._is_free,
        }

    @property
    def event(self):
        """Return the next upcoming event."""
        return self._event

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    async def async_get_events(self, hass, start_date, end_date):
        """Get all events in a specific time frame."""
        _LOGGER.debug("Running ICalCalendarEventDevice async get events")
        return await self.ical_events.async_get_events(hass, start_date, end_date)

    async def async_update(self):
        """Update event data."""
        _LOGGER.debug("Running ICalCalendarEventDevice async update for %s", self.name)
        await self.ical_events.update()
        event = copy.deepcopy(self.ical_events.event)
        if event is None:
            self._event = event
            return
        event["summary"] += " !!-2" # Manually set offset to 2 mins prior
        event = calculate_offset(event, OFFSET)
        self._event = copy.deepcopy(event)
        self._event["start"] = {}
        self._event["end"] = {}
        self._event["start"]["dateTime"] = event["start"].isoformat()
        self._event["end"]["dateTime"] = event["end"].isoformat()
        self._offset_reached = is_offset_reached(self.event)
        self._event["all_day"] = event["all_day"]
