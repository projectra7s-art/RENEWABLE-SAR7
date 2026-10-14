"""Site elevation (metres above sea level) for any point on Earth.

Providers, tried in this order until one answers:
  1. Open-Meteo Elevation API (Copernicus DEM GLO-90, 90 m grid)
  2. OpenTopoData SRTM 90 m (land between 60 N and 56 S)
  3. OpenTopoData ASTER 30 m (global land)
All are free and need no API key. Attribution is shown in the page footer.
If none answers, None is returned and the caller falls back to the elevation
NASA POWER returns with the weather data.
"""

import requests

TIMEOUT_SECONDS = 8

OPEN_METEO_URL = "https://api.open-meteo.com/v1/elevation"
OPEN_TOPO_URL = "https://api.opentopodata.org/v1/{dataset}"


def _to_float(value):
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _open_meteo(lat, lon):
    response = requests.get(
        OPEN_METEO_URL,
        params={"latitude": lat, "longitude": lon},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return _to_float(response.json().get("elevation"))


def _open_topo(dataset):
    def lookup(lat, lon):
        response = requests.get(
            OPEN_TOPO_URL.format(dataset=dataset),
            params={"locations": f"{lat},{lon}"},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json().get("results") or []
        return _to_float(results[0].get("elevation")) if results else None

    return lookup


PROVIDERS = (
    _open_meteo,
    _open_topo("srtm90m"),
    _open_topo("aster30m"),
)


def get_elevation(lat: float, lon: float):
    """Elevation in metres, or None if no provider could give it."""
    for provider in PROVIDERS:
        try:
            value = provider(lat, lon)
        except (requests.RequestException, ValueError, TypeError, KeyError):
            continue
        if value is not None:
            return value

    return None
