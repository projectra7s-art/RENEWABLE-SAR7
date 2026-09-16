import math
import random
from config import PV, WIND, BATTERY, SYSTEM, PSO


# ============================================================
# WIND TURBINE MODEL
# ============================================================

def wind_power_kw(v: float) -> float:
    """Generic wind turbine power curve."""

    cut_in = WIND["cut_in_mps"]
    rated_v = WIND["rated_mps"]
    cut_out = WIND["cut_out_mps"]
    rated_p = WIND["rated_kw"]

    if v < cut_in or v >= cut_out:
        return 0.0

    if v >= rated_v:
        return rated_p

    numerator = v**3 - cut_in**3
    denominator = rated_v**3 - cut_in**3

    return rated_p * numerator / denominator


# ============================================================
# LOAD PROFILE
# ============================================================

def build_load_profile(monthly_kwh: float, n: int):
    """
    Build a generic residential hourly load profile.

    Annual energy target:
        monthly_kwh × 12
    """

    shape = [
        0.020, 0.019, 0.018, 0.017, 0.017, 0.020,
        0.024, 0.032, 0.038, 0.040, 0.041, 0.042,
        0.043, 0.044, 0.046, 0.050, 0.058, 0.068,
        0.081, 0.095, 0.090, 0.076, 0.055, 0.031,
    ]

    daily_sum = sum(shape)

    annual_load = monthly_kwh * 12.0

    days = n / 24.0

    daily_energy = annual_load / max(days, 1.0)

    load = []

    for i in range(n):

        hour = i % 24

        load.append(
            (shape[hour] / daily_sum)
            * daily_energy
        )

    return load


# ============================================================
# HOURLY SYSTEM SIMULATION
# ============================================================

def simulate(
    x,
    weather,
    monthly_kwh,
    target_renewable_fraction=0.90
):

    pv_count, wt_count, bat_count = x

    solar = weather["solar_irradiance"]
    wind = weather["wind_speed"]

    n = min(
        len(solar),
        len(wind)
    )

    if n == 0:
        raise RuntimeError(
            "No valid weather data available."
        )

    load = build_load_profile(
        monthly_kwh,
        n
    )

    # ========================================================
    # COMPONENT SIZES
    # ========================================================

    pv_kw_each = (
        PV["rated_w"] / 1000.0
    )

    battery_capacity = (
        bat_count
        * BATTERY["usable_kwh"]
    )

    min_soc = (
        battery_capacity
        * BATTERY["minimum_soc"]
    )

    soc = (
        battery_capacity
        * BATTERY["initial_soc"]
    )

    # ========================================================
    # ENERGY VARIABLES
    # ========================================================

    total_load = 0.0

    renewable_direct = 0.0
    renewable_to_battery = 0.0
    battery_to_load = 0.0

    grid = 0.0
    unmet = 0.0
    curtailed = 0.0
    renewable_generated = 0.0

    sample = []

    battery_eff = (
        BATTERY["round_trip_efficiency"]
    )

    sqrt_eff = math.sqrt(
        battery_eff
    )

    # ========================================================
    # HOURLY SIMULATION
    # ========================================================

    for i in range(n):

        # ----------------------------------------------------
        # PV GENERATION
        # ----------------------------------------------------

        pv = (
            pv_count
            * pv_kw_each
            * (solar[i] / 1000.0)
            * PV["performance_factor"]
        )

        # ----------------------------------------------------
        # WIND GENERATION
        # ----------------------------------------------------

        wind_gen = (
            wt_count
            * wind_power_kw(
                wind[i]
            )
        )

        renewable = max(
            0.0,
            pv + wind_gen
        )

        demand = max(
            0.0,
            load[i]
        )

        total_load += demand

        renewable_generated += renewable

        # ----------------------------------------------------
        # RENEWABLE → LOAD
        # ----------------------------------------------------

        served_direct = min(
            renewable,
            demand
        )

        renewable_direct += (
            served_direct
        )

        deficit = (
            demand
            - served_direct
        )

        surplus = (
            renewable
            - served_direct
        )

        # ----------------------------------------------------
        # RENEWABLE → BATTERY
        # ----------------------------------------------------

        if (
            battery_capacity > 0
            and surplus > 0
        ):

            available_capacity = (
                battery_capacity
                - soc
            )

            charge = min(
                surplus,
                max(
                    0.0,
                    available_capacity
                    / sqrt_eff
                )
            )

            soc = min(
                battery_capacity,
                soc
                + charge * sqrt_eff
            )

            renewable_to_battery += (
                charge
            )

            surplus -= charge

        # ----------------------------------------------------
        # CURTAILMENT
        # ----------------------------------------------------

        curtailed += max(
            0.0,
            surplus
        )

        # ----------------------------------------------------
        # BATTERY → LOAD
        # ----------------------------------------------------

        if (
            deficit > 0
            and battery_capacity > 0
        ):

            available = max(
                0.0,
                soc - min_soc
            )

            discharge = min(
                deficit,
                available * sqrt_eff
            )

            soc = max(
                min_soc,
                soc
                - discharge / sqrt_eff
            )

            battery_to_load += (
                discharge
            )

            deficit -= discharge

        # ----------------------------------------------------
        # GRID → LOAD
        # ----------------------------------------------------

        if deficit > 0:

            grid += deficit

        # ----------------------------------------------------
        # HOURLY CHART DATA
        # ----------------------------------------------------

        sample.append({

            "load": demand,

            "renewable": renewable,

            "grid": max(
                0.0,
                deficit
            ),

            "soc": (
                soc
                / battery_capacity
                * 100.0
                if battery_capacity > 0
                else 0.0
            ),
        })

    # ========================================================
    # RENEWABLE CONTRIBUTION
    # ========================================================

    renewable_served = (
        renewable_direct
        + battery_to_load
    )

    renewable_fraction = (
        renewable_served
        / total_load
        if total_load > 0
        else 0.0
    )

    grid_share = (
        grid
        / total_load
        if total_load > 0
        else 0.0
    )

    # ========================================================
    # CAPITAL COST
    # ========================================================

    capital_cost = (

        pv_count
        * PV["price_sar"]

        + wt_count
        * WIND["price_sar"]

        + bat_count
        * BATTERY["price_sar"]
    )

    if pv_count + wt_count > 0:

        capital_cost += (
            SYSTEM["inverter_cost_sar"]
        )

    if (
        pv_count
        + wt_count
        + bat_count
        > 0
    ):

        capital_cost += (
            SYSTEM[
                "balance_of_system_cost_sar"
            ]
        )

    # ========================================================
    # GRID COST
    # ========================================================

    grid_tariff = SYSTEM.get(
        "grid_tariff_sar_per_kwh",
        0.18
    )

    annual_grid_cost = (
        grid
        * grid_tariff
    )

    # ========================================================
    # USER RENEWABLE TARGET
    # ========================================================

    target_fraction = max(
        0.0,
        min(
            1.0,
            float(
                target_renewable_fraction
            )
        )
    )

    target_energy = (
        total_load
        * target_fraction
    )

    renewable_shortfall = max(
        0.0,
        target_energy
        - renewable_served
    )

    # ========================================================
    # OBJECTIVE FUNCTION
    #
    # Priority:
    # 1. No unserved energy
    # 2. Reach user's renewable target
    # 3. Minimize equipment cost
    # 4. Minimize grid electricity cost
    # 5. Reduce wasted energy
    # ========================================================

    objective = (

        1_000_000.0
        * unmet

        + 500.0
        * renewable_shortfall

        + capital_cost

        + annual_grid_cost

        + 0.05
        * curtailed
    )

    return {

        "objective": objective,

        "capital_cost": capital_cost,

        "annual_grid_cost": annual_grid_cost,

        "total_load": total_load,

        "renewable_generated":
            renewable_generated,

        "renewable_served":
            renewable_served,

        "renewable_direct":
            renewable_direct,

        "renewable_to_battery":
            renewable_to_battery,

        "battery_to_load":
            battery_to_load,

        "grid": grid,

        "unmet": unmet,

        "curtailed": curtailed,

        "renewable_fraction":
            max(
                0.0,
                min(
                    1.0,
                    renewable_fraction
                )
            ),

        "grid_share":
            max(
                0.0,
                min(
                    1.0,
                    grid_share
                )
            ),

        "renewable_shortfall":
            renewable_shortfall,

        "sample": sample,
    }


# ============================================================
# PSO OPTIMIZATION
# ============================================================

def optimize_system(
    weather,
    monthly_kwh,
    target_renewable_fraction=0.90
):

    """
    Integer Particle Swarm Optimization.

    Decision variables:

        x[0] = PV panels
        x[1] = wind turbines
        x[2] = battery units
    """

    bounds = [

        (
            0,
            SYSTEM["max_pv_panels"]
        ),

        (
            0,
            SYSTEM["max_wind_turbines"]
        ),

        (
            0,
            SYSTEM["max_batteries"]
        ),
    ]

    rng = random.Random(
        PSO["seed"]
    )

    particles = []

    # ========================================================
    # INTEGER CLAMP
    # ========================================================

    def clamp_round(
        value,
        idx
    ):

        low, high = bounds[idx]

        return int(
            max(
                low,
                min(
                    high,
                    round(value)
                )
            )
        )

    # ========================================================
    # INITIAL SWARM
    # ========================================================

    for _ in range(
        PSO["particles"]
    ):

        x = [

            rng.randint(
                lo,
                hi
            )

            for lo, hi in bounds
        ]

        v = [

            rng.uniform(
                -2.5,
                2.5
            )

            for _ in range(3)
        ]

        result = simulate(

            x,
            weather,
            monthly_kwh,

            # IMPORTANT:
            # Pass user's target
            target_renewable_fraction
        )

        particles.append({

            "x": x,

            "v": v,

            "best_x": x[:],

            "best_score":
                result["objective"],
        })

    # ========================================================
    # GLOBAL BEST
    # ========================================================

    gbest = min(
        particles,
        key=lambda p:
            p["best_score"]
    )

    global_x = (
        gbest["best_x"][:]
    )

    global_score = (
        gbest["best_score"]
    )

    # ========================================================
    # PSO ITERATIONS
    # ========================================================

    for _ in range(
        PSO["iterations"]
    ):

        for p in particles:

            for j in range(3):

                r1 = rng.random()
                r2 = rng.random()

                p["v"][j] = (

                    PSO["inertia"]
                    * p["v"][j]

                    + PSO["cognitive"]
                    * r1
                    * (
                        p["best_x"][j]
                        - p["x"][j]
                    )

                    + PSO["social"]
                    * r2
                    * (
                        global_x[j]
                        - p["x"][j]
                    )
                )

                p["x"][j] = (
                    clamp_round(
                        p["x"][j]
                        + p["v"][j],
                        j
                    )
                )

            # IMPORTANT:
            # Pass target during every PSO evaluation

            result = simulate(

                p["x"],
                weather,
                monthly_kwh,

                target_renewable_fraction
            )

            if (
                result["objective"]
                < p["best_score"]
            ):

                p["best_x"] = (
                    p["x"][:]
                )

                p["best_score"] = (
                    result["objective"]
                )

                if (
                    result["objective"]
                    < global_score
                ):

                    global_score = (
                        result["objective"]
                    )

                    global_x = (
                        p["x"][:]
                    )

    # ========================================================
    # FINAL SYSTEM
    # ========================================================

    # IMPORTANT:
    # Pass target to final simulation too

    final = simulate(

        global_x,
        weather,
        monthly_kwh,

        target_renewable_fraction
    )

    # ========================================================
    # WEATHER
    # ========================================================

    avg_solar = (

        sum(
            weather[
                "solar_irradiance"
            ]
        )

        /

        len(
            weather[
                "solar_irradiance"
            ]
        )
    )

    avg_wind = (

        sum(
            weather[
                "wind_speed"
            ]
        )

        /

        len(
            weather[
                "wind_speed"
            ]
        )
    )

    # ========================================================
    # PERFORMANCE
    # ========================================================

    annual_load = (
        monthly_kwh * 12.0
    )

    renewable_fraction_pct = (
        final["renewable_fraction"]
        * 100.0
    )

    grid_share_pct = (
        final["grid_share"]
        * 100.0
    )

    # ========================================================
    # SOLAR ENERGY
    # ========================================================

    solar_generated_kwh = (

        global_x[0]

        * PV["rated_w"]
        / 1000.0

        * (
            sum(
                weather[
                    "solar_irradiance"
                ]
            )
            / 1000.0
        )

        * PV["performance_factor"]
    )

    # ========================================================
    # BATTERY DETAILS
    # ========================================================

    battery_unit_kwh = (
        BATTERY["usable_kwh"]
    )

    total_battery_kwh = (

        global_x[2]
        * battery_unit_kwh
    )

    usable_battery_kwh = (

        total_battery_kwh

        * (
            1.0
            - BATTERY["minimum_soc"]
        )
    )

    # ========================================================
    # CHART
    # ========================================================

    sample = final["sample"]

    chart_slice = sample[:24]

    # ========================================================
    # SYSTEM TYPE
    # ========================================================

    if (
        global_x[0] > 0
        and global_x[1] > 0
        and global_x[2] > 0
    ):

        system_type = (
            "PV + Wind + Battery"
        )

    elif (
        global_x[0] > 0
        and global_x[2] > 0
    ):

        system_type = (
            "PV + Battery"
        )

    elif (
        global_x[1] > 0
        and global_x[2] > 0
    ):

        system_type = (
            "Wind + Battery"
        )

    elif (
        global_x[0] > 0
        and global_x[1] > 0
    ):

        system_type = (
            "PV + Wind"
        )

    elif global_x[0] > 0:

        system_type = "PV"

    elif global_x[1] > 0:

        system_type = "Wind"

    elif global_x[2] > 0:

        system_type = "Battery"

    else:

        system_type = "Grid Only"

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "recommended": {

            "pv_panels":
                global_x[0],

            "pv_kw": round(
                global_x[0]
                * PV["rated_w"]
                / 1000.0,
                2
            ),

            "wind_turbines":
                global_x[1],

            "wind_kw": round(
                global_x[1]
                * WIND["rated_kw"],
                2
            ),

            "battery_units":
                global_x[2],

            "battery_kwh":
                round(
                    total_battery_kwh,
                    2
                ),

            "battery_unit_kwh":
                round(
                    battery_unit_kwh,
                    2
                ),

            "battery_usable_kwh":
                round(
                    usable_battery_kwh,
                    2
                ),

            "system_type":
                system_type,
        },

        "economics": {

            "capital_cost_sar":
                round(
                    final["capital_cost"],
                    0
                ),

            "annual_grid_energy_kwh":
                round(
                    final["grid"],
                    0
                ),

            "annual_unserved_kwh":
                round(
                    final["unmet"],
                    0
                ),

            "curtailed_kwh":
                round(
                    final["curtailed"],
                    0
                ),

            "estimated_annual_grid_cost_sar":
                round(
                    final["annual_grid_cost"],
                    0
                ),
        },

        "performance": {

            "renewable_fraction_pct":
                round(
                    renewable_fraction_pct,
                    1
                ),

            "grid_share_pct":
                round(
                    max(
                        0.0,
                        grid_share_pct
                    ),
                    1
                ),

            "solar_generated_kwh":
                round(
                    solar_generated_kwh,
                    0
                ),

            "renewable_generated_kwh":
                round(
                    final[
                        "renewable_generated"
                    ],
                    0
                ),

            "renewable_served_kwh":
                round(
                    final[
                        "renewable_served"
                    ],
                    0
                ),

            "renewable_target_pct":
                round(
                    target_fraction_for_display(
                        target_renewable_fraction
                    ),
                    1
                ),
        },

        "weather": {

            "year":
                weather["year"],

            "valid_hours":
                weather["hours"],

            "average_solar":
                round(
                    avg_solar,
                    3
                ),

            "average_wind_mps":
                round(
                    avg_wind,
                    3
                ),
        },

        "chart": {

            "hours":
                list(range(24)),

            "load": [
                round(
                    x["load"],
                    3
                )
                for x in chart_slice
            ],

            "renewable": [
                round(
                    x["renewable"],
                    3
                )
                for x in chart_slice
            ],

            "grid": [
                round(
                    x["grid"],
                    3
                )
                for x in chart_slice
            ],
        },

        "assumptions": {

            "pv_w":
                PV["rated_w"],

            "wind_kw":
                WIND["rated_kw"],

            "battery_kwh":
                BATTERY["usable_kwh"],

            "battery_efficiency_pct":
                BATTERY[
                    "round_trip_efficiency"
                ] * 100.0,

            "target_renewable_pct":
                target_renewable_fraction
                * 100.0,
        },
    }


def target_fraction_for_display(value):
    """Keep target percentage inside 0–100%."""

    return (
        max(
            0.0,
            min(
                1.0,
                float(value)
            )
        )
        * 100.0
    )