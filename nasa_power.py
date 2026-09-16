import requests

NASA_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"

def get_nasa_hourly(lat: float, lon: float, year: int = 2025) -> dict:
    """
    NASA POWER hourly point query.

    Solar parameter:
      ALLSKY_SFC_SW_DWN = All Sky Surface Shortwave Downward Irradiance
    Wind parameter:
      WS10M = Wind Speed at 10 m

    The site requests one calendar year and uses the returned valid hourly
    records for the optimization.
    """
    start = f"{year}0101"
    end = f"{year}1231"

    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,WS10M",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": start,
        "end": end,
        "format": "JSON",
        "time-standard": "LST",
    }

    response = requests.get(NASA_URL, params=params, timeout=90)
    response.raise_for_status()
    data = response.json()

    try:
        p = data["properties"]["parameter"]
        solar_map = p["ALLSKY_SFC_SW_DWN"]
        wind_map = p["WS10M"]
    except KeyError as exc:
        raise RuntimeError(f"NASA POWER response is missing {exc}")

    keys = sorted(set(solar_map) & set(wind_map))
    if not keys:
        raise RuntimeError("NASA POWER did not return hourly records.")

    solar = []
    wind = []
    valid_keys = []

    for key in keys:
        s = solar_map.get(key)
        w = wind_map.get(key)

        # NASA POWER uses -999/-999.0 for missing values.
        if s is None or w is None or float(s) <= -900 or float(w) <= -900:
            continue

        solar.append(max(0.0, float(s)))
        wind.append(max(0.0, float(w)))
        valid_keys.append(key)

    if len(solar) < 100:
        raise RuntimeError("Too few valid NASA POWER records were returned.")

    return {
        "year": year,
        "solar_irradiance": solar,
        "wind_speed": wind,
        "timestamps": valid_keys,
        "hours": len(solar),
    }
