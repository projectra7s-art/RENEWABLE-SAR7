"""Physical models used to prepare the simulation.

- PV panel output (with cell-temperature loss)
- wind: shear to hub height, air density, power curve
- hourly load profile (12 monthly values, or an hourly file)
- selected equipment
"""

import math

from config import (
    BATTERY_OPTIONS,
    LOAD_PROFILE,
    PV_OPTIONS,
    SELECTED,
    SITE,
    WIND_OPTIONS,
)


DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
HOURS_IN_YEAR = 8760
HOURS_IN_LEAP_YEAR = 8784

R_AIR = 287.05           # J/(kg K)
SEA_LEVEL_PRESSURE = 101325.0


def clamp(value, low, high):
    return max(low, min(high, value))


def clamp_round(value, low, high):
    return int(clamp(round(value), low, high))


# ------------------------------------------------------------
# PV
# ------------------------------------------------------------

def pv_panel_kw(pv: dict, irradiance_w_m2: float, ambient_c: float) -> float:
    """Output (kW) of ONE panel.

    rated x (G / 1000) x temperature factor x performance factor
    where the cell temperature is  T_amb + (NOCT - 20) / 800 * G.
    """
    if ambient_c is None:
        temp_factor = 1.0  # temperature ignored (config SITE["use_temperature"])
    else:
        cell_c = ambient_c + (pv["noct_c"] - 20.0) / 800.0 * irradiance_w_m2
        temp_factor = max(0.0, 1.0 + pv["temp_coeff_per_c"] * (cell_c - 25.0))

    return (
        (pv["rated_w"] / 1000.0)
        * (irradiance_w_m2 / 1000.0)
        * temp_factor
        * pv["performance_factor"]
    )


# ------------------------------------------------------------
# Wind
# ------------------------------------------------------------

def wind_power_kw(v: float, turbine: dict) -> float:
    """Simplified wind-turbine power curve (kW for ONE turbine).

    v < cut-in or v >= cut-out : 0
    cut-in <= v < rated        : cubic interpolation
    rated  <= v < cut-out      : rated power
    """
    cut_in = turbine["cut_in_mps"]
    rated_v = turbine["rated_mps"]
    cut_out = turbine["cut_out_mps"]
    rated_p = turbine["rated_kw"]

    if v < cut_in or v >= cut_out:
        return 0.0

    if v >= rated_v:
        return rated_p

    denominator = rated_v**3 - cut_in**3
    if denominator <= 0:
        return 0.0

    return rated_p * ((v**3 - cut_in**3) / denominator)


def shear_exponent(ws_lower, ws_upper):
    """Site wind-shear exponent from the mean NASA speeds at 10 m and 50 m.

    Returns (alpha, source). Falls back to the configured default when the
    50 m data is missing.
    """
    default = SITE["default_shear_exponent"]

    if not ws_lower or not ws_upper:
        return default, "default"

    mean_lower = sum(ws_lower) / len(ws_lower)
    mean_upper = sum(ws_upper) / len(ws_upper)

    if mean_lower <= 0.1 or mean_upper <= 0.1:
        return default, "default"

    alpha = math.log(mean_upper / mean_lower) / math.log(
        SITE["wind_upper_height_m"] / SITE["wind_lower_height_m"]
    )
    low, high = SITE["shear_exponent_limits"]

    return clamp(alpha, low, high), "NASA WS10M/WS50M"


def hub_speed_factor(hub_height_m: float, alpha: float) -> float:
    """Multiply the 10 m speed by this factor to get the hub-height speed."""
    return (hub_height_m / SITE["wind_lower_height_m"]) ** alpha


def isa_temperature_c(elevation_m: float) -> float:
    return 15.0 - 0.0065 * elevation_m


def air_density(elevation_m: float, temp_c: float) -> float:
    """Air density (kg/m3) from site elevation and air temperature."""
    pressure = SEA_LEVEL_PRESSURE * (1.0 - 2.25577e-5 * elevation_m) ** 5.25588
    return pressure / (R_AIR * (temp_c + 273.15))


def density_speed_factor(rho: float) -> float:
    """Speed normalization to the reference density (IEC 61400-12)."""
    return (rho / SITE["reference_air_density"]) ** (1.0 / 3.0)


# ------------------------------------------------------------
# Selected equipment (PSO decides only the quantities)
# ------------------------------------------------------------

def selected_components(overrides=None):
    """The fixed PV / wind / battery models chosen in config.SELECTED.

    overrides (optional, from the form):
        pv_performance_factor  replaces the PV performance factor
        battery_efficiency     replaces the battery round-trip efficiency
    """
    overrides = overrides or {}

    def pick(options, key):
        for option in options:
            if option["id"] == SELECTED[key]:
                return dict(option)  # copy: never modify the catalogue
        raise KeyError(
            f"config.SELECTED['{key}'] = '{SELECTED[key]}' is not in its catalogue"
        )

    pv = pick(PV_OPTIONS, "pv")
    wind = pick(WIND_OPTIONS, "wind")
    battery = pick(BATTERY_OPTIONS, "battery")

    # temperature ignored -> the performance factor must include its loss
    if not SITE["use_temperature"] and "performance_factor_temp_ignored" in pv:
        pv["performance_factor"] = pv["performance_factor_temp_ignored"]

    if overrides.get("pv_performance_factor") is not None:
        pv["performance_factor"] = float(overrides["pv_performance_factor"])

    if overrides.get("battery_efficiency") is not None:
        battery["round_trip_efficiency"] = float(overrides["battery_efficiency"])

    return {"pv": pv, "wind": wind, "battery": battery}


# ------------------------------------------------------------
# Calendar helpers
# ------------------------------------------------------------

def _month_of_day(day_index: int) -> int:
    """0-based month for a 0-based day of the year (non-leap calendar)."""
    remaining = day_index
    for month, days in enumerate(DAYS_IN_MONTH):
        if remaining < days:
            return month
        remaining -= days
    return 11


def calendar_positions(n: int, timestamps=None):
    """(months, hours) for every simulated hour.

    Taken from the NASA timestamps (YYYYMMDDHH) when available, otherwise
    from the hour index. month is 0..11, hour is 0..23.
    """
    months, hours = [], []
    for i in range(n):
        if timestamps and i < len(timestamps):
            stamp = str(timestamps[i])
            months.append(int(stamp[4:6]) - 1)
            hours.append(int(stamp[8:10]))
        else:
            months.append(_month_of_day(i // 24))
            hours.append(i % 24)
    return months, hours


def _hour_of_year(stamp: str, leap_file: bool):
    """Position of a NASA timestamp inside an hourly file (None = no slot)."""
    month = int(stamp[4:6])
    day = int(stamp[6:8])
    hour = int(stamp[8:10])

    if month == 2 and day == 29 and not leap_file:
        return None

    days_before = sum(DAYS_IN_MONTH[: month - 1])
    if leap_file and month > 2:
        days_before += 1

    return (days_before + day - 1) * 24 + hour


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

def build_monthly_load(monthly_kwh, months, hours) -> list:
    """Hourly load (kWh) from 12 monthly totals.

    Each month's energy is spread over that month's hours with the 24-hour
    shape, so the total of every month is exactly the value given.
    """
    shape = LOAD_PROFILE["hourly_shape"]
    shape_sum = sum(shape)

    weights = [shape[h] / shape_sum for h in hours]

    month_weight = [0.0] * 12
    for m, w in zip(months, weights):
        month_weight[m] += w

    return [
        monthly_kwh[m] * w / month_weight[m] if month_weight[m] > 0 else 0.0
        for m, w in zip(months, weights)
    ]


def build_file_load(values, timestamps, n):
    """Hourly load from a user file of 8760 (or 8784) hourly values.

    The file starts at 1 January 00:00. Every NASA hour is matched with its
    slot in the file by date and hour, so hours removed from the NASA data
    (or 29 February) never shift the rest. Returns (load, keep) where `keep`
    lists the NASA hour indices that have a value in the file (None = all).
    """
    if len(values) not in (HOURS_IN_YEAR, HOURS_IN_LEAP_YEAR):
        raise ValueError("file_length")

    if not timestamps:
        if len(values) != n:
            raise ValueError("file_length")
        return list(values), None

    leap_file = len(values) == HOURS_IN_LEAP_YEAR
    load, keep = [], []

    for i in range(n):
        index = _hour_of_year(str(timestamps[i]), leap_file)
        if index is None or index >= len(values):
            continue
        load.append(values[index])
        keep.append(i)

    if not keep:
        raise ValueError("file_length")

    return load, (None if len(keep) == n else keep)
