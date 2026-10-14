"""Turn the final simulation into the JSON-friendly dict sent to the UI."""

from config import SYSTEM

from .economics import annual_cost_per_unit, cost_table


def system_type(pv_count, wind_count, battery_count):
    if pv_count > 0 and wind_count > 0 and battery_count > 0:
        return "PV + Wind + Battery"
    if pv_count > 0 and battery_count > 0:
        return "PV + Battery"
    if wind_count > 0 and battery_count > 0:
        return "Wind + Battery"
    if pv_count > 0 and wind_count > 0:
        return "PV + Wind"
    if pv_count > 0:
        return "PV"
    if wind_count > 0:
        return "Wind"
    if battery_count > 0:
        return "Battery"
    return "Grid Only"


def target_fraction_for_display(value):
    """0.90 -> 90.0 (clamped to 0..100)."""
    return max(0.0, min(1.0, float(value))) * 100.0


# ------------------------------------------------------------
# Average day (chart)
# ------------------------------------------------------------

SERIES = ("load", "renewable", "grid", "soc")


def _average_days(sample, months, hours):
    """Average value of every hour of the day.

    Uses ALL simulated hours (not only the first 24): once over the whole
    year and once for each month. Hour and month come from the NASA
    timestamps, so they stay correct even if NASA dropped some hours.
    """
    def empty():
        return {key: [0.0] * 24 for key in SERIES}

    year_sum, year_count = empty(), [0] * 24
    month_sum = [empty() for _ in range(12)]
    month_count = [[0] * 24 for _ in range(12)]

    for item, month, hour in zip(sample, months, hours):
        year_count[hour] += 1
        month_count[month][hour] += 1
        for key in SERIES:
            year_sum[key][hour] += item[key]
            month_sum[month][key][hour] += item[key]

    def mean(total, count):
        return {
            key: [
                round(total[key][h] / count[h], 3) if count[h] else 0.0
                for h in range(24)
            ]
            for key in SERIES
        }

    return (
        mean(year_sum, year_count),
        [mean(month_sum[m], month_count[m]) for m in range(12)],
    )


# ------------------------------------------------------------
# Why PV or wind? cost of one generated kWh at this site
# ------------------------------------------------------------

def _energy_cost_comparison(site):
    """Generator only (no battery / inverter / BOS), annualized with the
    component lifetime. Explains why the optimizer prefers one technology."""
    def one(option, unit_output, category):
        annual_kwh = sum(unit_output)
        if annual_kwh <= 0:
            return {
                "type": option["id"],
                "sar_per_kwh": None,
                "annual_kwh_per_unit": 0.0,
            }
        cost = annual_cost_per_unit(category, option["price_sar"])
        return {
            "type": option["id"],
            "sar_per_kwh": round(cost / annual_kwh, 4),
            "annual_kwh_per_unit": round(annual_kwh, 0),
        }

    components = site["components"]
    return {
        "pv": one(components["pv"], site["pv_unit"], "pv"),
        "wind": one(components["wind"], site["wind_unit"], "wind"),
    }


# ------------------------------------------------------------
# Site-level report (same for every scenario)
# ------------------------------------------------------------

def build_site_report(site, target_renewable_fraction, year):
    info = site["info"]
    components = site["components"]
    pv = components["pv"]
    turbine = components["wind"]
    battery = components["battery"]

    average_kw = info["annual_load_kwh"] / max(1, info["hours_used"])

    return {
        "weather": {
            "year": year,
            "valid_hours": info["hours_used"],
            "average_solar": round(info["average_solar"], 3),
            "average_wind_mps": round(info["average_wind_10m"], 3),
            "average_wind_hub_mps": round(info["average_wind_hub_mps"], 3),
            "average_temp_c": (
                round(info["average_temp_c"], 1)
                if info["average_temp_c"] is not None
                else None
            ),
            "elevation_m": round(info["elevation_m"], 0),
            "elevation_source": info["elevation_source"],
            "air_density_kg_m3": round(info["average_air_density"], 3),
            "wind_shear_exponent": round(info["shear_exponent"], 3),
            "wind_shear_source": info["shear_source"],
            "temperature_source": info["temperature_source"],
            "temperature_correction_c": round(info["temperature_correction_c"], 1),
        },

        "load": {
            "type": info["load_type"],
            "annual_kwh": round(info["annual_load_kwh"], 1),
            "monthly_kwh": round(info["annual_load_kwh"] / 12.0, 1),
            "average_kw": round(average_kw, 2),
            "monthly_kwh_list": [
                round(v, 1) for v in info["monthly_load_kwh"]
            ],
        },

        "comparison": _energy_cost_comparison(site),

        "assumptions": {
            "pv_type": pv["id"],
            "pv_w": pv["rated_w"],
            "pv_price_sar": pv["price_sar"],
            "pv_performance_factor": pv["performance_factor"],
            "wind_type": turbine["id"],
            "wind_kw": turbine["rated_kw"],
            "wind_price_sar": turbine["price_sar"],
            "wind_hub_height_m": turbine["hub_height_m"],
            "battery_type": battery["id"],
            "battery_kwh": battery["usable_kwh"],
            "battery_price_sar": battery["price_sar"],
            "battery_efficiency_pct": battery["round_trip_efficiency"] * 100.0,
            "target_renewable_pct": target_renewable_fraction * 100.0,
        },

        "optimization": {
            "method": "PSO (number of PV / wind / battery units) + Local Search",
            "objective_design": (
                "Annualized capital + Grid - Export + Target + Curtailment"
            ),
        },
    }


# ------------------------------------------------------------
# Scenario report
# ------------------------------------------------------------

def build_scenario_report(final, site, target_renewable_fraction):
    pv = final["pv"]
    turbine = final["wind"]
    battery = final["battery"]

    pv_count = final["pv_count"]
    wind_count = final["wind_count"]
    battery_count = final["battery_count"]

    solar_generated_kwh = pv_count * sum(site["pv_unit"])
    wind_generated_kwh = wind_count * sum(site["wind_unit"])

    total_battery_kwh = battery_count * battery["usable_kwh"]

    year_profile, month_profiles = _average_days(
        final["sample"], site["months"], site["hours"]
    )

    # monthly totals (kWh): production by source, load, energy from the grid
    solar_month, wind_month = [0.0] * 12, [0.0] * 12
    load_month, grid_month = [0.0] * 12, [0.0] * 12
    for i, month in enumerate(site["months"]):
        solar_month[month] += pv_count * site["pv_unit"][i]
        wind_month[month] += wind_count * site["wind_unit"][i]
        load_month[month] += site["load"][i]
        grid_month[month] += final["sample"][i]["grid"]

    # share of the demand served by each source. Battery energy is attributed
    # to solar / wind in proportion to how much each one generated.
    renewable_share = final["renewable_fraction"] * 100.0
    generated = solar_generated_kwh + wind_generated_kwh
    solar_part = solar_generated_kwh / generated if generated > 0 else 0.0
    energy_mix = {
        "solar_pct": round(renewable_share * solar_part, 1),
        "wind_pct": round(renewable_share * (1.0 - solar_part), 1)
        if generated > 0 else 0.0,
        "grid_pct": round(max(0.0, final["grid_share"] * 100.0), 1),
    }

    # ---- money: itemized table + yearly total + comparison with the grid
    table = cost_table(final)
    annual_load = site["info"]["annual_load_kwh"]
    total_year = final["annual_total_cost"]

    costs = dict(table)
    costs.update({
        "grid_cost_sar": round(final["annual_grid_cost"], 0),
        "export_revenue_sar": round(final["export_revenue"], 0),
        "total_year_sar": round(total_year, 0),
        "electricity_cost_sar_per_kwh": round(total_year / annual_load, 3)
        if annual_load > 0 else None,
    })

    # a scenario that reaches the maximum allowed quantity of something and
    # still misses the target is not feasible within the configured limits
    limits_hit = [
        name for name, count, maximum in (
            ("pv", pv_count, SYSTEM["max_pv_panels"]),
            ("wind", wind_count, SYSTEM["max_wind_turbines"]),
            ("battery", battery_count, SYSTEM["max_batteries"]),
        ) if count >= maximum
    ]

    return {
        "recommended": {
            "pv_type": pv["id"],
            "pv_panels": pv_count,
            "pv_panel_w": pv["rated_w"],
            "pv_kw": round(pv_count * pv["rated_w"] / 1000.0, 2),

            "wind_type": turbine["id"],
            "wind_turbines": wind_count,
            "wind_turbine_kw": turbine["rated_kw"],
            "wind_hub_height_m": turbine["hub_height_m"],
            "wind_kw": round(wind_count * turbine["rated_kw"], 2),

            "battery_type": battery["id"],
            "battery_units": battery_count,
            "battery_unit_kwh": round(battery["usable_kwh"], 2),
            "battery_kwh": round(total_battery_kwh, 2),
            "battery_nominal_kwh": round(final["battery_nominal_kwh"], 2),

            "system_type": system_type(pv_count, wind_count, battery_count),
        },

        "economics": {
            "capital_cost_sar": round(final["capital_cost"], 0),
            "annualized_capital_sar": round(final["annualized_capital"], 0),
            "annual_total_cost_sar": round(final["annual_total_cost"], 0),
            "annual_grid_energy_kwh": round(final["grid"], 0),
            "annual_unserved_kwh": round(final["unmet"], 0),
            "curtailed_kwh": round(final["curtailed"], 0),
            "export_revenue_sar": round(final["export_revenue"], 0),
            "estimated_annual_grid_cost_sar": round(
                final["annual_grid_cost"], 0
            ),
        },

        "performance": {
            "renewable_fraction_pct": round(
                final["renewable_fraction"] * 100.0, 1
            ),
            "grid_share_pct": round(
                max(0.0, final["grid_share"] * 100.0), 1
            ),
            "target_met": bool(
                final["renewable_fraction"]
                >= min(1.0, target_renewable_fraction) - 1e-9
            ),
            "solar_generated_kwh": round(solar_generated_kwh, 0),
            "wind_generated_kwh": round(wind_generated_kwh, 0),
            "renewable_generated_kwh": round(
                final["renewable_generated"], 0
            ),
            "renewable_served_kwh": round(final["renewable_served"], 0),
            "renewable_target_pct": round(
                target_fraction_for_display(target_renewable_fraction), 1
            ),
        },

        "costs": costs,

        "limits_hit": limits_hit,

        "monthly": {
            "solar_kwh": [round(v, 1) for v in solar_month],
            "wind_kwh": [round(v, 1) for v in wind_month],
            "load_kwh": [round(v, 1) for v in load_month],
            "grid_kwh": [round(v, 1) for v in grid_month],
        },

        "energy_mix": energy_mix,

        "chart": {
            "hours": list(range(24)),
            "load": year_profile["load"],
            "renewable": year_profile["renewable"],
            "grid": year_profile["grid"],
            "soc": year_profile["soc"],
            "months": month_profiles,
        },

        "objective": round(final["objective"], 2),
    }
