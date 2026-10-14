"""Hourly simulation of ONE candidate system + its objective value.

Decision vector `x` (see pso.py) - only QUANTITIES; the equipment models are
fixed in config.SELECTED:
    x[0] number of PV panels
    x[1] number of wind turbines
    x[2] number of batteries
"""

import math

from config import OBJECTIVE, SYSTEM

from .components import clamp_round
from .economics import annualized_capital, capital_breakdown, total_capital


# ------------------------------------------------------------
# 1) Decode a particle into real equipment
# ------------------------------------------------------------

def decode_particle(x, components):
    return {
        "pv_count": clamp_round(x[0], 0, SYSTEM["max_pv_panels"]),
        "wind_count": clamp_round(x[1], 0, SYSTEM["max_wind_turbines"]),
        "battery_count": clamp_round(x[2], 0, SYSTEM["max_batteries"]),
        "pv": components["pv"],
        "wind": components["wind"],
        "battery": components["battery"],
    }


# ------------------------------------------------------------
# 2) Hourly energy dispatch (renewables -> load -> battery -> grid)
# ------------------------------------------------------------

def _run_dispatch(design, site, record_sample):
    battery = design["battery"]

    pv_count = design["pv_count"]
    wind_count = design["wind_count"]

    load = site["load"]
    pv_unit = site["pv_unit"]      # kW per panel, hour by hour
    wind_unit = site["wind_unit"]  # kW per turbine, hour by hour

    # usable_kwh is what the owner can really use, so the nominal capacity is
    # larger by 1 / (1 - minimum_soc); the SOC window [min, 100%] then
    # delivers exactly count x usable_kwh.
    nominal_per_unit = battery["usable_kwh"] / (1.0 - battery["minimum_soc"])
    battery_capacity = design["battery_count"] * nominal_per_unit
    min_soc = battery_capacity * battery["minimum_soc"]
    soc = battery_capacity * battery["initial_soc"]

    # sqrt(round-trip efficiency) is applied on charge AND on discharge.
    sqrt_eff = math.sqrt(battery["round_trip_efficiency"])

    total_load = 0.0
    renewable_generated = 0.0
    renewable_direct = 0.0
    renewable_to_battery = 0.0
    battery_to_load = 0.0
    grid = 0.0
    curtailed = 0.0
    sample = []

    for i in range(len(load)):
        # --- generation (per-unit hourly output x quantity) --
        pv_generation = pv_count * pv_unit[i]
        wind_generation = wind_count * wind_unit[i]

        renewable = max(0.0, pv_generation + wind_generation)
        demand = max(0.0, load[i])

        total_load += demand
        renewable_generated += renewable

        # --- renewable -> load ------------------------------
        served_direct = min(renewable, demand)
        renewable_direct += served_direct

        deficit = demand - served_direct
        surplus = renewable - served_direct

        # --- renewable surplus -> battery -------------------
        if battery_capacity > 0 and surplus > 0:
            available_capacity = battery_capacity - soc
            charge = min(surplus, max(0.0, available_capacity / sqrt_eff))
            soc = min(battery_capacity, soc + charge * sqrt_eff)

            renewable_to_battery += charge
            surplus -= charge

        # --- whatever is left is curtailed ------------------
        curtailed += max(0.0, surplus)

        # --- battery -> load --------------------------------
        if deficit > 0 and battery_capacity > 0:
            available = max(0.0, soc - min_soc)
            discharge = min(deficit, available * sqrt_eff)
            soc = max(min_soc, soc - discharge / sqrt_eff)

            battery_to_load += discharge
            deficit -= discharge

        # --- grid covers the rest ---------------------------
        if deficit > 0:
            grid += deficit

        if record_sample:
            sample.append({
                "load": demand,
                "renewable": renewable,
                "grid": max(0.0, deficit),
                "soc": (
                    soc / battery_capacity * 100.0
                    if battery_capacity > 0
                    else 0.0
                ),
            })

    return {
        "total_load": total_load,
        "renewable_generated": renewable_generated,
        "renewable_direct": renewable_direct,
        "renewable_to_battery": renewable_to_battery,
        "battery_to_load": battery_to_load,
        "grid": grid,
        "curtailed": curtailed,
        "battery_capacity": battery_capacity,
        "sample": sample,
    }


# ------------------------------------------------------------
# 3) Objective (lower is better, SAR/year) -- weights in config.OBJECTIVE
# ------------------------------------------------------------

def _objective(energy, annual_capital, target_fraction, renewable_served):
    total_load = energy["total_load"]
    grid = energy["grid"]
    curtailed = energy["curtailed"]
    renewable_generated = energy["renewable_generated"]
    battery_capacity = energy["battery_capacity"]

    # NOTE: `unmet` is always 0 because the grid covers any deficit.
    # The term is kept so the objective can be extended later.
    unmet = 0.0
    unmet_penalty = OBJECTIVE["unmet_penalty_per_kwh"] * unmet

    target_energy = total_load * target_fraction
    renewable_shortfall = max(0.0, target_energy - renewable_served)
    target_penalty = (
        OBJECTIVE["renewable_shortfall_penalty_per_kwh"] * renewable_shortfall
    )

    annual_grid_cost = grid * SYSTEM.get("grid_tariff_sar_per_kwh", 0.18)
    grid_penalty = annual_grid_cost

    curtailment_ratio = curtailed / max(total_load, 1.0)

    # Surplus that nobody can use is exported (grid-tied). It earns the
    # feed-in tariff (0 by default); it is only "wasted" when unpaid.
    feed_in = SYSTEM.get("feed_in_tariff_sar_per_kwh", 0.0)
    export_revenue = curtailed * feed_in
    curtailment_penalty = (
        OBJECTIVE["curtailment_penalty_per_kwh"] * curtailed
        if feed_in <= 0
        else 0.0
    )

    # Some extra generation is allowed because renewable energy is
    # produced at different times from the load.
    allowed_generation = (
        max(target_fraction, OBJECTIVE["generation_min_target"])
        * total_load
        * OBJECTIVE["generation_allowed_margin"]
    )
    excess_generation = max(0.0, renewable_generated - allowed_generation)
    generation_oversize_penalty = (
        OBJECTIVE["generation_oversize_penalty_per_kwh"] * excess_generation
    )

    average_daily_load = total_load / 365.0
    battery_ratio = battery_capacity / max(average_daily_load, 1.0)
    battery_excess_days = max(0.0, battery_ratio - 1.0)
    battery_oversize_penalty = (
        OBJECTIVE["battery_oversize_penalty_per_day"] * battery_excess_days
    )

    objective = (
        unmet_penalty
        + target_penalty
        + annual_capital
        + grid_penalty
        - export_revenue
        + curtailment_penalty
        + generation_oversize_penalty
        + battery_oversize_penalty
    )

    return {
        "objective": objective,
        "unmet": unmet,
        "annual_grid_cost": annual_grid_cost,
        "export_revenue": export_revenue,
        "renewable_shortfall": renewable_shortfall,
        "curtailment_ratio": curtailment_ratio,
        "generation_oversize_penalty": generation_oversize_penalty,
        "battery_oversize_penalty": battery_oversize_penalty,
    }


def capital_of(x, site):
    """Capital cost of a decision vector (no simulation needed)."""
    design = decode_particle(x, site["components"])
    return total_capital(capital_breakdown(design))


# ------------------------------------------------------------
# 4) Public entry point
# ------------------------------------------------------------

def simulate(
    x,
    site,
    target_renewable_fraction=0.90,
    record_sample=True,
):
    """Simulate one candidate system and return energy, cost and objective.

    `site` comes from build_site(). `record_sample=False` skips the
    per-hour chart data (faster during the search); numbers are identical.
    """
    design = decode_particle(x, site["components"])

    energy = _run_dispatch(design, site, record_sample)

    total_load = energy["total_load"]
    renewable_served = energy["renewable_direct"] + energy["battery_to_load"]

    renewable_fraction = (
        renewable_served / total_load if total_load > 0 else 0.0
    )
    grid_share = energy["grid"] / total_load if total_load > 0 else 0.0

    target_fraction = max(0.0, min(1.0, float(target_renewable_fraction)))

    breakdown = capital_breakdown(design)
    capital = total_capital(breakdown)
    annual_capital = annualized_capital(breakdown)

    terms = _objective(energy, annual_capital, target_fraction, renewable_served)

    return {
        "objective": terms["objective"],
        "capital_cost": capital,
        "capital_breakdown": breakdown,
        "annualized_capital": annual_capital,
        "annual_grid_cost": terms["annual_grid_cost"],
        "export_revenue": terms["export_revenue"],
        "annual_total_cost": (
            annual_capital + terms["annual_grid_cost"] - terms["export_revenue"]
        ),
        "total_load": total_load,
        "renewable_generated": energy["renewable_generated"],
        "renewable_served": renewable_served,
        "renewable_direct": energy["renewable_direct"],
        "renewable_to_battery": energy["renewable_to_battery"],
        "battery_to_load": energy["battery_to_load"],
        "grid": energy["grid"],
        "unmet": terms["unmet"],
        "curtailed": energy["curtailed"],
        "renewable_fraction": max(0.0, min(1.0, renewable_fraction)),
        "grid_share": max(0.0, min(1.0, grid_share)),
        "renewable_shortfall": terms["renewable_shortfall"],
        "curtailment_ratio": terms["curtailment_ratio"],
        "generation_oversize_penalty": terms["generation_oversize_penalty"],
        "battery_oversize_penalty": terms["battery_oversize_penalty"],
        "sample": energy["sample"],
        "pv": design["pv"],
        "wind": design["wind"],
        "battery": design["battery"],
        "battery_nominal_kwh": energy["battery_capacity"],
        "pv_count": design["pv_count"],
        "wind_count": design["wind_count"],
        "battery_count": design["battery_count"],
    }
