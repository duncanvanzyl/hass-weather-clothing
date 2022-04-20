"""Constants for the Outdoor Clothes integration."""

from collections import OrderedDict

DOMAIN = "clothing"

DEFAULT_JACKET_CONFIG = OrderedDict(
    [
        ("Winter Jacket", ["temperature < 5"]),
        ("Rain Jacket", ["precipitation_probability > 20", "temperature >= 5"]),
        ("Jacket", ["temperature < 15"]),
        ("Long Sleeves", ["temperature < 20", "temperature >= 15"]),
        ("Short Sleeves", ["temperature > 20"]),
    ]
)

DEFAULT_PANTS_CONFIG = OrderedDict(
    [
        ("Snow Pants", ["temperature < -2"]),
        ("Rain Pants", ["precipitation_probability > 40"]),
        ("Pants", ["temperature >= -2", "temperature < 17"]),
        ("Shorts", ["temperature >= 17"]),
    ]
)
DEFAULT_BOOTS_CONFIG = OrderedDict(
    [
        ("Winter Boots", ["temperature < 5"]),
        ("Rain Boots", ["precipitation_probability > 20"]),
        ("Shoes", ["temperature >= 5"]),
    ]
)

ATTR_FORECAST = "forecast"
CONF_JACKET = "jacket"
CONF_PANTS = "pants"
CONF_BOOTS = "boots"
CONF_CONFIG_KEY = "config"
