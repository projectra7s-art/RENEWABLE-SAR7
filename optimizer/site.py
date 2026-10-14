"""Site context: everything that depends on the weather and the load but NOT
on the number of components. It is built once per analysis, so the PSO only
has to multiply the hourly per-unit outputs by the candidate quantities.

    load[i]      kWh in hour i
    pv_unit[i]   kW of ONE selected PV panel
    wind_unit[i] kW of ONE selected wind turbine
    months[i], hours[i]  calendar position of hour i (0..11, 0..23)
"""

from config import SITE

from .components import (
    air_density,
    build_file_load,
    build_monthly_load,
    calendar_positions,
    density_speed_factor,
    hub_speed_factor,
    isa_temperature_c,
    pv_panel_kw,
    selected_components,
    shear_exponent,
    wind_power_kw,
)


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _subset(values, keep):
    return [values[i] for i in keep] if values else values


def build_site(
    weather,
    load_spec,
    elevation_m=None,
    elevation_source="user",
    overrides=None,
):
    """weather + load -> hourly site model.

    load_spec = {"type": "monthly", "monthly_kwh": [12 values]}
              | {"type": "file",    "values": [8760 (or 8784) hourly kWh]}
    """
    solar = weather["solar_irradiance"]
    wind10 = weather["wind_speed"]
    n = min(len(solar), len(wind10))

    if n == 0:
        raise RuntimeError("No valid weather data available.")

    solar = solar[:n]
    wind10 = wind10[:n]
    temperature = weather.get("temperature_c")
    temperature = temperature[:n] if temperature else None
    wind50 = weather.get("wind_speed_50m")
    wind50 = wind50[:n] if wind50 else None
    timestamps = weather.get("timestamps")
    timestamps = list(timestamps)[:n] if timestamps else None

    # --- load -------------------------------------------------
    if load_spec["type"] == "file":
        load, keep = build_file_load(load_spec["values"], timestamps, n)

        if keep is not None:  # weather hours without a slot in the file
            solar = _subset(solar, keep)
            wind10 = _subset(wind10, keep)
            temperature = _subset(temperature, keep)
            wind50 = _subset(wind50, keep)
            timestamps = _subset(timestamps, keep)
            n = len(keep)

        months, hours = calendar_positions(n, timestamps)
    else:
        months, hours = calendar_positions(n, timestamps)
        load = build_monthly_load(load_spec["monthly_kwh"], months, hours)

    # --- elevation --------------------------------------------
    if elevation_m is not None:
        elevation = float(elevation_m)
    elif weather.get("elevation_m") is not None:
        elevation, elevation_source = float(weather["elevation_m"]), "NASA"
    else:
        elevation, elevation_source = 0.0, "default"

    # --- hourly ambient temperature ---------------------------
    temperature_correction = 0.0
    use_temperature = SITE["use_temperature"] and bool(temperature)

    if not SITE["use_temperature"]:
        ambient = None                      # temperature is ignored
        temperature_source = "ignored"
    elif temperature:
        ambient = list(temperature)
        temperature_source = "NASA T2M"

        # NASA's temperature belongs to the elevation of its grid cell: move
        # it to the real site elevation with the standard lapse rate.
        nasa_elevation = weather.get("elevation_m")
        if SITE["lapse_rate_correction"] and nasa_elevation is not None:
            temperature_correction = -SITE["lapse_rate_c_per_m"] * (
                elevation - float(nasa_elevation)
            )
            ambient = [t + temperature_correction for t in ambient]
            if abs(temperature_correction) >= 0.05:
                temperature_source = "NASA T2M (site elevation)"
    else:
        ambient = [SITE["fallback_ambient_c"]] * n
        temperature_source = "default"

    # --- hourly air density -----------------------------------
    if SITE["apply_air_density"]:
        if use_temperature:
            density = [air_density(elevation, t) for t in ambient]
        else:
            density = [air_density(elevation, isa_temperature_c(elevation))] * n
    else:
        density = [SITE["reference_air_density"]] * n

    density_factor = [density_speed_factor(rho) for rho in density]

    # --- wind shear -------------------------------------------
    alpha, alpha_source = shear_exponent(wind10, wind50)

    # --- per-unit hourly outputs (selected equipment) ---------
    components = selected_components(overrides)
    pv = components["pv"]
    turbine = components["wind"]

    pv_unit = [
        pv_panel_kw(pv, solar[i], ambient[i] if ambient is not None else None)
        for i in range(n)
    ]

    shear = hub_speed_factor(turbine["hub_height_m"], alpha)
    wind_unit = [
        wind_power_kw(wind10[i] * shear * density_factor[i], turbine)
        for i in range(n)
    ]

    monthly_load = [0.0] * 12
    for m, value in zip(months, load):
        monthly_load[m] += value

    return {
        "n": n,
        "load": load,
        "pv_unit": pv_unit,
        "wind_unit": wind_unit,
        "months": months,
        "hours": hours,
        "components": components,
        "info": {
            "load_type": load_spec["type"],
            "annual_load_kwh": sum(load),
            "monthly_load_kwh": monthly_load,
            "elevation_m": elevation,
            "elevation_source": elevation_source,
            "temperature_source": temperature_source,
            "temperature_correction_c": temperature_correction,
            "average_temp_c": _mean(ambient) if use_temperature else None,
            "average_air_density": _mean(density),
            "shear_exponent": alpha,
            "shear_source": alpha_source,
            "average_wind_hub_mps": _mean(wind10) * shear,
            "average_solar": _mean(solar),
            "average_wind_10m": _mean(wind10),
            "hours_used": n,
        },
    }
