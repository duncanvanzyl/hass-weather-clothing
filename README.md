# Outside Clothing

Recommends clothing based on the weather forecast.

## Configuration

- __name__: Friendly name of the sensor.
- __entity_id__: Weather entity supplying the forcast.
- __unique_id__: Unique ID for customizing the sensor. (_Optional_)
- __selector__: A series of clothing items and the conditions under which they
    would be appropriate. See [Selector](#Selector) for more details. (_Optional_ but if you don't use it, then you must have __default__)
- __default__: One of the default sets of selectors. See [Default](#Default) for more details. (_Optional_ but if you don't use it, then you must have __selector__)
    - jacket
    - pants
    - boots

_Example_:

```yaml
sensor:
  - platform: clothing
    name: Jacket
    entity_id: weather.montreal_hourly
    default: jacket
  - platform: clothing
    name: Pants
    entity_id: weather.montreal_hourly
    selector:
      "Snow Pants":
      - temperature < -2
      "Rain Pants":
      - precipitation_probability > 40
      "Pants":
      - temperature >= -2
      - temperature < 17
      "Shorts":
      - temperature >= 17
  - platform: clothing
    name: Default Pants
    entity_id: weather.montreal_hourly
    default: pants
  - platform: clothing
    name: Boots
    entity_id: weather.montreal_hourly
    selector:
      "Winter Boots":
      - temperature < 5
      "Rain Boots":
      - precipitation_probability > 20
      "Shoes":
      - temperature >= 5
```

## Selector

Selector allows you to set appropriate outerwear (or anything else really) based
on forecast conditions. The format is a named clothing item as a key with a list
of weather conditions (criteria) that need to be met for that clothing item to
be appropriate. All criteria must be met for the clothing to be recommended.

```yaml
"<clothing item>:
- <criteria 1>
- <criteria 2>
```

### Criteria

Criteria must be in the form: `<forecast key> <operator> <value>`.

#### Forecast Key

The forecast keys are any key that a forecast provides. Current keys are:
- `datetime` (_though this one isn't super helpful_)
- `temperature`
- `condition`
- `precipitation_probability`

#### Operator

The standard comparison operators you might expect are supported:
- `<` - Forecast is less than value
- `<=` - Forecast is less than or equal to value
- `==` - Forecast is equal to value
- `>=` - Forecast is greater than or equal to value
- `>` - Forecast is greater than value
- `!=` - Forecast is not equal to value

#### Value

Value can be either a `string` or a `float`. This allows the criteria to be, for
example:
`temperature < 5` or `temperature < 5.5` or `condition == sunny`

> For __string comparisons__, they are just that. So while `cloudy < sunny` is true,
it probably isn't all that useful to do string comparisons with operators other
than `==` and `!=`.

## Default

There are three defaults with reasonable values for clothing:

- Jacket: This is a set of outerwear worn on your upper body. 😉
    The selectors this matches to are:
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
    The selectors this matches to are:
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
    The selectors this matches to are:
    ```yaml
    "Winter Boots":
    - temperature < 5
    "Rain Boots":
    - precipitation_probability > 20
    "Shoes":
    - temperature >= 5
    ```