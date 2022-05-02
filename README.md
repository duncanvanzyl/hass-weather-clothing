# Outside Clothing

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Sensors that recommend clothing based on the weather forecast.

## Features
- Display names (clothing items) configurable per sensor.
- Criteria configurable per sensor.
- Default values.
- Works with both daily forecasts and hourly foercasts.
- Configurable time ranges for criteria per sensor.
- Provides both a sensor and a binary_sensor platform.

## Sensor Configuration

- __name__: Friendly name of the sensor.
- __entity_id__: Weather entity supplying the forcast (either _hourly_ or
    _daily_).
- __unique_id__: Unique ID for customizing the sensor.  
    (_Optional_)
- __conditions__: A series of clothing items and the conditions under which they
    would be appropriate. See [Sensor Conditons](#sensor-conditions) for more
    details.  
    (_Optional_ but if you don't use it, then you must have __default__)
- __default__: One of the default sets of conditions. See [Sensor Defaults](#sensor-defaults) 
    for more details.  
    (_Optional_ but if you don't use it, then you must have __conditions__)
    - `jacket`
    - `pants`
    - `boots`
    > Only avaliable for __sensor__.  
- __mode__: Either a shorthand or the number of hours to consider from the
    forecast. See [Mode](#mode) for more details.  
    (_Optional_: Defaults to _hour_)
    - `hour`
    - `day`
    - `hours: <hours in range 1 - 24>`

_Example_:

```yaml
sensor:
  - platform: clothing
    name: Jacket
    entity_id: weather.montreal_hourly
    unique_id: default_jacket
    default: jacket

  - platform: clothing
    name: Pants
    entity_id: weather.montreal_hourly
    conditions:
      "Snow Pants":
      - temperature < -2
      "Rain Pants":
      - precipitation_probability > 40
      "Pants":
      - temperature >= -2
      - temperature < 17
      "Shorts":
      - temperature >= 17
    mode: hour

  - platform: clothing
    name: Default Pants
    entity_id: weather.montreal_hourly
    default: pants
    mode: day

  - platform: clothing
    name: Boots
    entity_id: weather.montreal_hourly
    conditions:
      "Winter Boots":
      - temperature < 5
      "Rain Boots":
      - precipitation_probability > 20
      "Shoes":
      - temperature >= 5
    mode:
      hours: 24
```

## Sensor Conditions

Conditions allows you to set appropriate outerwear (or anything else really) based
on forecast conditions. The format is a named clothing item as a key with a list
of weather conditions (criteria) that need to be met for that clothing item to
be appropriate. All criteria must be met for the clothing to be recommended.

```yaml
"<clothing item>:
- <criteria 1>
- <criteria 2>
```


## Sensor Defaults

There are three defaults with reasonable values for clothing:

- Jacket: This is a set of outerwear worn on your upper body. 😉  
    The conditions this matches are:
    ```yaml
    "Winter Jacket":
    - temperature < 5
    "Rain Jacket":
    - precipitation_probability > 20
    - temperature >= 5
    "Jacket":
    - temperature < 15
    "Long Sleeves":
    - temperature < 20
    - temperature >= 15
    "Short Sleeves":
    - temperature > 20
    ```
- Pants: This is a set of outerwear worn on your legs.  
    The conditions this matches are:
    ```yaml
    "Snow Pants":
    - temperature < -2
    "Rain Pants":
    - precipitation_probability > 40
    "Pants":
    - temperature >= -2
    - temperature < 17
    "Shorts":
    - temperature >= 17
    ```
- Boots: These are things to wear on your feet.  
    The conditions this matches are:
    ```yaml
    "Winter Boots":
    - temperature < 5
    "Rain Boots":
    - precipitation_probability > 20
    "Shoes":
    - temperature >= 5
    ```

## Bianry Sensor Configuration

- __name__: Friendly name of the sensor.
- __entity_id__: Weather entity supplying the forcast (either _hourly_ or
    _daily_).
- __unique_id__: Unique ID for customizing the sensor.  
    (_Optional_)
- __conditions__: A list of conditions for which the sensor will be set. See
    [Binary Sensor Conditons](#binary-sensor-conditions) for more details.  
    (_Optional_ but if you don't use it, then you must have __default__)
- __mode__: Either a shorthand or the number of hours to consider from the
    forecast. See [Mode](#mode) for more details.  
    (_Optional_: Defaults to _hour_)
    - `hour`
    - `day`
    - `hours: <hours in range 1 - 24>`

_Example_:

```yaml
binary_sensor:
  - platform: clothing
    name: Mow the Grass now
    entity_id: weather.ottawa_richmond_metcalfe_hourly
    unique_id: mow_grass
    conditions:
      - temperature > 5
      - precipitation_probability < 20
    mode:
      hours: 4
```

## Binary Sensor Conditions

Conditions allows you to set the binary sensor based on the forecast. The format
is a list of weather conditions (criteria) that need to be met for binary sensor
to be set. All criteria must be met for the binary sensor to be set.

```yaml
- <criteria 1>
- <criteria 2>
```

## Criteria

Criteria must be in the form: `<forecast key> <operator> <value>`.

### Forecast Key

The forecast keys are any key that a forecast provides. Current keys are:
- `datetime` (_though this one isn't super helpful_)
- `temperature`
- `condition`
- `precipitation_probability`

### Operator

The standard comparison operators you might expect are supported:
- `<` - Forecast is less than value
- `<=` - Forecast is less than or equal to value
- `==` - Forecast is equal to value
- `>=` - Forecast is greater than or equal to value
- `>` - Forecast is greater than value
- `!=` - Forecast is not equal to value

### Value

Value can be either a `string` or a `float`. This allows the criteria to be, for
example:
`temperature < 5` or `temperature < 5.5` or `condition == sunny`

> For __string comparisons__, they are just that. So while `cloudy < sunny` is
true, it probably isn't all that useful to do string comparisons with operators
other than `==` and `!=`.

## Mode

There are several modes that determine how many hours of the forecast to
consider.
- `hour` - Takes into consideration only the next hour.
- `day` - Considers the next 10 hours. Or about how long you might be resonably
    expected to be outside for the day.
- `hours: <hours in range 1 - 24>` - Considers how many hours you want to
    specify up to 24.

> In the case that __entity_id__ is a _daily_ forecast, the mode doesn't
matter as it only considers today. Though this has not been tested on all
possible weather integrations.
