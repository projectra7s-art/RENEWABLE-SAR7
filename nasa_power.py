import requests

NASA_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"

# Required: solar + wind at 10 m.
BASE_PARAMETERS = ("ALLSKY_SFC_SW_DWN", "WS10M")

# Optional (better physics): air temperature and wind at 50 m.
# If NASA rejects them the request is repeated with BASE_PARAMETERS only
# and the model falls back to default assumptions from config.py.
EXTRA_PARAMETERS = ("T2M", "WS50M")

MISSING = -900  # NASA POWER uses -999 for missing values


def _request(lat, lon, year, parameters):
    params = {
        "parameters": ",".join(parameters),
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": f"{year}0101",
        "end": f"{year}1231",
        "format": "JSON",
        "time-standard": "LST",
    }

    response = requests.get(NASA_URL, params=params, timeout=90)
    response.raise_for_status()
    return response.json()


def _optional_series(parameter_map, keys):
    """Values aligned with `keys`; missing hours are filled with the mean.

    Returns None when the parameter has no valid value at all.
    """
    values = []
    for key in keys:
        raw = parameter_map.get(key)
        values.append(None if raw is None or float(raw) <= MISSING else float(raw))

    valid = [v for v in values if v is not None]
    if not valid:
        return None

    mean = sum(valid) / len(valid)
    return [mean if v is None else v for v in values]


def _parse(data, year, with_extras):
    try:
        p = data["properties"]["parameter"]
        solar_map = p["ALLSKY_SFC_SW_DWN"]
        wind_map = p["WS10M"]
        temp_map = p["T2M"] if with_extras else None
        wind50_map = p["WS50M"] if with_extras else None
    except KeyError as exc:
        raise KeyError(f"NASA POWER response is missing {exc}")

    keys = sorted(set(solar_map) & set(wind_map))
    if not keys:
        raise RuntimeError("NASA POWER did not return hourly records.")

    solar, wind, valid_keys = [], [], []

    for key in keys:
        s = solar_map.get(key)
        w = wind_map.get(key)

        if s is None or w is None or float(s) <= MISSING or float(w) <= MISSING:
            continue

        solar.append(max(0.0, float(s)))
        wind.append(max(0.0, float(w)))
        valid_keys.append(key)

    if len(solar) < 100:
        raise RuntimeError("Too few valid NASA POWER records were returned.")

    temperature = wind50 = None
    if with_extras:
        temperature = _optional_series(temp_map, valid_keys)
        wind50 = _optional_series(wind50_map, valid_keys)
        if wind50:
            wind50 = [max(0.0, v) for v in wind50]

    # elevation of the NASA grid cell: geometry.coordinates = [lon, lat, elev]
    elevation = None
    try:
        coordinates = data["geometry"]["coordinates"]
        if len(coordinates) >= 3 and coordinates[2] is not None:
            elevation = float(coordinates[2])
    except (KeyError, TypeError, ValueError):
        pass

    return {
        "year": year,
        "solar_irradiance": solar,      # W/m2
        "wind_speed": wind,             # m/s at 10 m
        "wind_speed_50m": wind50,       # m/s at 50 m (or None)
        "temperature_c": temperature,   # degC at 2 m (or None)
        "elevation_m": elevation,       # m above sea level (or None)
        "timestamps": valid_keys,
        "hours": len(solar),
    }


def get_nasa_hourly(lat: float, lon: float, year: int = 2025) -> dict:
    """NASA POWER hourly point query for one calendar year.

    ALLSKY_SFC_SW_DWN = All Sky Surface Shortwave Downward Irradiance
    WS10M / WS50M     = Wind speed at 10 m / 50 m above ground
    T2M               = Air temperature at 2 m
    """
    try:
        data = _request(lat, lon, year, BASE_PARAMETERS + EXTRA_PARAMETERS)
        return _parse(data, year, with_extras=True)
    except (requests.HTTPError, KeyError):
        # the optional parameters are not available: use the required ones
        data = _request(lat, lon, year, BASE_PARAMETERS)
        try:
            return _parse(data, year, with_extras=False)
        except KeyError as exc:
            raise RuntimeError(str(exc))
