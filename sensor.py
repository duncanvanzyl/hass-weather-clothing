from __future__ import annotations

import logging
from collections import OrderedDict
from math import ceil
from typing import Any, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.components.weather import ATTR_FORECAST
from homeassistant.components.weather import DOMAIN as WEATHER_DOMAIN
from homeassistant.const import (
    CONF_CONDITIONS,
    CONF_DEFAULT,
    CONF_ENTITY_ID,
    CONF_MODE,
    CONF_NAME,
    CONF_UNIQUE_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, State
from homeassistant.exceptions import IntegrationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from weather_clothing.clothing_item import ClothingItem

from .const import (
    ATTR_FORECAST,
    CONF_HOURS,
    CONF_SELECTOR_KEY,
    DEFAULT_BOOTS_CONFIG,
    DEFAULT_JACKET_CONFIG,
    DEFAULT_PANTS_CONFIG,
    MIN_CONFIDENCE,
    OPTION_BOOTS,
    OPTION_DAY,
    OPTION_HOUR,
    OPTION_JACKET,
    OPTION_PANTS,
)
from .helpers import clothing_from_config, hours_from_forecast

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_ENTITY_ID): cv.entity_domain(WEATHER_DOMAIN),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Exclusive(CONF_CONDITIONS, CONF_SELECTOR_KEY): OrderedDict([(str, [str])]),
        vol.Exclusive(CONF_DEFAULT, CONF_SELECTOR_KEY): vol.Any(
            OPTION_JACKET, OPTION_PANTS, OPTION_BOOTS
        ),
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
    """Set up the sensor platform."""

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

    conditions = config.get(CONF_CONDITIONS)
    if conditions is None:
        default = config[CONF_DEFAULT]
        if default == OPTION_JACKET:
            conditions = DEFAULT_JACKET_CONFIG
        elif default == OPTION_PANTS:
            conditions = DEFAULT_PANTS_CONFIG
        elif default == OPTION_BOOTS:
            conditions = DEFAULT_BOOTS_CONFIG
        else:
            raise IntegrationError(f"Could not create clothing sensor: {name}")

    sensor = ClothingSensor(name, hours, conditions, unique_id)

    async_track_state_change_event(hass, entity_id, sensor.listen_event)

    add_entities([sensor])


class ClothingSensor(SensorEntity):
    """Representation of a Clothing Sensor."""

    _attr_icon = "mdi:tshirt-crew"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _clothing: str = STATE_UNKNOWN
    _confidence: float = 0
    _n: int = 0

    def __init__(
        self,
        name: str,
        hours: int,
        conditions: OrderedDict[str, list[str]],
        unique_id: Optional[str],
    ) -> None:
        self._attr_name = name
        self._hours = hours
        self._conditions = conditions
        self._attr_unique_id = unique_id

    def predict(self, forecast: list[dict[str, Any]]) -> None:
        """Predict the appropriate clothing based on the forecast."""
        # TODO: This is an ass backwards way of setting the minimum confidence.
        # It might be better to update the weather_clothing library.
        min_count = ceil(MIN_CONFIDENCE * len(forecast))

        items: list[ClothingItem] = clothing_from_config(self._conditions, min_count)

        for item in items:
            for prediction in forecast:
                try:
                    if item.meets_criteria(prediction):
                        item.inc()
                except TypeError as err:
                    _LOGGER.error("WTF: Error: %s, Forecast: %s", err, forecast)
            if item.value is not None:
                self._clothing = item.name
                self._confidence = item.confidence
                self._n = len(forecast)

                return
        self._clothing = STATE_UNKNOWN

    def listen_event(self, event: Event) -> None:
        """Callback for when an event occurs."""
        new_state: State = event.data["new_state"]

        if new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._clothing = STATE_UNAVAILABLE
            return

        if (forecast := new_state.attributes.get(ATTR_FORECAST)) is None:
            self._clothing = STATE_UNAVAILABLE
            return

        forecast = hours_from_forecast(forecast, self._hours)

        self.predict(forecast)

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_native_value = self._clothing
        self._attr_available = self._clothing != STATE_UNAVAILABLE

        if self._clothing in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._attr_extra_state_attributes = {}
            return

        self._attr_extra_state_attributes = {
            "confidence": self._confidence,
            "n": self._n,
        }
