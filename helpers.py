from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.weather import ATTR_FORECAST_TIME
from homeassistant.util import dt as dt_util
from weather_clothing.clothing_item import ClothingItem
from weather_clothing.comparisons import operator_map as om


def clothing_from_config(
    config: dict[str, Any], min_count: int = 1
) -> list[ClothingItem]:
    """Convert a dictionary of clothing items and criteria into a list of
    ClothingItems.
    """
    clothing_items: list[ClothingItem] = []
    priority: int = 0
    for item in config:
        comparisons = [
            om.comparison_from_string(comparison) for comparison in config[item]
        ]
        clothing_items.append(ClothingItem(item, priority, comparisons, min_count))
        priority += 1
    return clothing_items


def hours_from_forecast(
    forecast: list[dict[str, Any]], hours: int = 1
) -> list[dict[str, Any]]:
    """Get the hours of the forecast that are relent."""
    now = dt_util.now()
    diff = timedelta(hours=hours)

    trimmed_forecast: list[dict[str, Any]] = []

    for prediction in forecast:
        # Environment Canada integration returns datetime objects for hourly
        # forecast, and isoformatted strings for daily forecasts. So fix them
        # here.
        # TODO: Fix the Environment Canada integration.
        if isinstance(prediction[ATTR_FORECAST_TIME], datetime):
            prediction_time: datetime = prediction[ATTR_FORECAST_TIME]
            prediction[ATTR_FORECAST_TIME] = prediction_time.isoformat()
        elif isinstance(prediction[ATTR_FORECAST_TIME], str):
            prediction_time = datetime.fromisoformat(prediction[ATTR_FORECAST_TIME])
        else:
            raise ValueError(
                f"forecast '{ATTR_FORECAST_TIME}' should be an iso formatted datetime string"
            )
        if prediction_time - now < diff:
            trimmed_forecast.append(prediction)

    return trimmed_forecast
