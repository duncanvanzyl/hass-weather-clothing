from __future__ import annotations

from collections import OrderedDict
import logging
from typing import Any, Optional

import voluptuous as vol
from weather_clothing.clothing_item import ClothingItem
from weather_clothing.comparisons import operator_map as om

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_DEFAULT,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_SELECTOR,
    CONF_UNIQUE_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, State
from homeassistant.exceptions import IntegrationError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    ATTR_FORECAST,
    CONF_BOOTS,
    CONF_CONFIG_KEY,
    CONF_JACKET,
    CONF_PANTS,
    DEFAULT_BOOTS_CONFIG,
    DEFAULT_JACKET_CONFIG,
    DEFAULT_PANTS_CONFIG,
)

_LOGGER = logging.getLogger(__name__)


# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_ENTITY_ID): cv.entity_domain("weather"),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Exclusive(CONF_SELECTOR, CONF_CONFIG_KEY): OrderedDict([(str, [str])]),
        vol.Exclusive(CONF_DEFAULT, CONF_CONFIG_KEY): vol.Any(
            CONF_JACKET, CONF_PANTS, CONF_BOOTS
        ),
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""

    name = config[CONF_NAME]
    entity_id = config[CONF_ENTITY_ID]
    unique_id = config.get(CONF_UNIQUE_ID)
    selector = config.get(CONF_SELECTOR)
    if selector is None:
        default = config[CONF_DEFAULT]
        if default == CONF_JACKET:
            selector = DEFAULT_JACKET_CONFIG
        elif default == CONF_PANTS:
            selector = DEFAULT_PANTS_CONFIG
        elif default == CONF_BOOTS:
            selector = DEFAULT_BOOTS_CONFIG
        else:
            raise IntegrationError(f"Could not create clothing sensor: {name}")

    sensor = ClothingSensor(name, selector, unique_id)

    async_track_state_change_event(hass, entity_id, sensor.listen_event)

    add_entities([sensor])


def clothing_from_config(config: dict[str, Any]) -> list[ClothingItem]:
    """Convert a dictionary of clothing items and criteria into a list of
    ClothingItems.
    """
    clothing_items: list[ClothingItem] = []
    count: int = 0
    for item in config:
        comparisons = [
            om.comparison_from_string(comparison) for comparison in config[item]
        ]
        clothing_items.append(ClothingItem(item, count, comparisons))
        count += 1
    return clothing_items


class ClothingSensor(SensorEntity):
    """Representation of a Clothing Sensor."""

    _attr_icon = "mdi:tshirt-crew"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _clothing: str = STATE_UNKNOWN
    _count: int = 0
    _n: int = 0

    def __init__(
        self,
        name: str,
        clothing_config: OrderedDict[str, list[str]],
        unique_id: Optional[str],
    ) -> None:
        self._attr_name = name
        self._clothing_config = clothing_config
        self._attr_unique_id = unique_id

    def predict(self, forecast: list[dict[str, Any]]) -> None:
        """Predict the appropriate clothing based on the forecast."""
        items: list[ClothingItem] = clothing_from_config(self._clothing_config)
        for item in items:
            for prediction in forecast:
                if item.meets_criteria(prediction):
                    item.inc()
            if item.value is not None:
                self._clothing = item.name
                self._n = len(forecast)
                self._count = item._count

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

        self.predict(forecast)

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_native_value = self._clothing
        self._attr_available = self._clothing != STATE_UNAVAILABLE

        if self._clothing in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._attr_extra_state_attributes = {}
            return

        self._attr_extra_state_attributes = {
            "confidence": self._count / self._n,
            "n": self._n,
        }
