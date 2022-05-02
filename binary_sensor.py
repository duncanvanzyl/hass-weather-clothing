from __future__ import annotations

import logging
from math import ceil
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
from homeassistant.components.weather import DOMAIN as WEATHER_DOMAIN
from homeassistant.const import (
    CONF_CONDITIONS,
    CONF_ENTITY_ID,
    CONF_MODE,
    CONF_NAME,
    CONF_UNIQUE_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, State
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from weather_clothing.clothing_item import ClothingItem
from weather_clothing.comparisons import operator_map as om

from .const import ATTR_FORECAST, CONF_HOURS, MIN_CONFIDENCE, OPTION_DAY, OPTION_HOUR
from .helpers import hours_from_forecast

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_ENTITY_ID): cv.entity_domain(WEATHER_DOMAIN),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Required(CONF_CONDITIONS): [str],
        vol.Optional(CONF_MODE, default=OPTION_HOUR): vol.Any(
            OPTION_DAY, OPTION_HOUR, {CONF_HOURS: vol.Range(min=1, max=24)}
        ),
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the binary sensor platform."""

    name = config[CONF_NAME]
    mode = config[CONF_MODE]
    if mode == OPTION_HOUR:
        hours = 1
    elif mode == OPTION_DAY:
        hours = 10
    else:
        hours = mode[CONF_HOURS]

    entity_id = config[CONF_ENTITY_ID]
    unique_id = config.get(CONF_UNIQUE_ID)

    conditions = config[CONF_CONDITIONS]

    binary_sensor = ForecastBinarySensor(name, hours, conditions, unique_id)

    async_track_state_change_event(hass, entity_id, binary_sensor.listen_event)

    add_entities([binary_sensor])


class ForecastBinarySensor(BinarySensorEntity):
    """Representation of a Forecast Binary Sensor."""

    def __init__(
        self,
        name: str,
        hours: int,
        conditions: list[str],
        unique_id: str | None,
    ) -> None:
        self._attr_name = name
        self._hours = hours
        self._conditions = conditions
        self._attr_unique_id = unique_id
        self._state: bool | None = None
        self._confidence: float = 0
        self._n: int = 0

    def predict(self, forecast: list[dict[str, Any]]) -> None:
        """Predict if the forecast meets the conditions."""
        # TODO: This is an ass backwards way of setting the minimum confidence.
        # It might be better to update the weather_clothing library.
        min_count = ceil(MIN_CONFIDENCE * len(forecast))

        comparisons = [
            om.comparison_from_string(comparison) for comparison in self._conditions
        ]
        criteria = ClothingItem("", 0, comparisons, min_count)

        for prediction in forecast:
            try:
                criteria.meets_criteria(prediction, auto=True)
            except TypeError as err:
                _LOGGER.error("WTF: Error: %s, Forecast: %s", err, forecast)

        self._state = criteria.value is not None
        # confidence from the library is how confident that the state is true,
        # so if the state is false then the confidence is the inverse of the
        # confidence that the state is true, since the confidence is not how
        # confident we are that the state is correct, not that it is true.
        self._confidence = (
            criteria.confidence if self._state else (1 - criteria.confidence)
        )
        self._n = criteria.n

    def listen_event(self, event: Event) -> None:
        """Callback for when an event occurs."""
        new_state: State = event.data["new_state"]

        if (
            new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN)
            or (forecast := new_state.attributes.get(ATTR_FORECAST)) is None
        ):
            self._state = None
            return

        forecast = hours_from_forecast(forecast, self._hours)
        self.predict(forecast)

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_is_on = self._state

        if self._state is None:
            self._attr_extra_state_attributes = {}
            return

        self._attr_extra_state_attributes = {
            "confidence": self._confidence,
            "n": self._n,
        }
