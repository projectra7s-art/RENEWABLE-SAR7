import math
import random

from config import (
    PV_OPTIONS,
    WIND_OPTIONS,
    BATTERY_OPTIONS,
    SYSTEM,
    PSO,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def clamp_round(value, low, high):
    return int(clamp(round(value), low, high))


# ============================================================
# WIND TURBINE MODEL
# ============================================================

def wind_power_kw(v: float, turbine: dict) -> float:
    """
    Simplified wind-turbine power curve.

    Below cut-in:
        0 kW

    From cut-in to rated speed:
        Cubic approximation

    From rated to cut-out:
        Rated power

    At/above cut-out:
        0 kW
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

    return rated_p * (
        (v**3 - cut_in**3) / denominator
    )


# ============================================================
# LOAD PROFILE
# ============================================================

def build_load_profile(monthly_kwh: float, n: int):
    """
    Generic residential hourly load profile.

    Annual load = monthly_kwh × 12.
    The 24-hour shape is repeated across the weather period.
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

    return [
        (shape[i % 24] / daily_sum) * daily_energy
        for i in range(n)
    ]


# ============================================================
# HOURLY SYSTEM SIMULATION
# ============================================================

def simulate(
    x,
    weather,
    monthly_kwh,
    target_renewable_fraction=0.90,
):
    """
    Simulate one candidate system.

    Decision vector:
        x[0] = PV type index
        x[1] = PV quantity
        x[2] = Wind type index
        x[3] = Wind quantity
        x[4] = Battery type index
        x[5] = Battery quantity
    """

    # --------------------------------------------------------
    # DECODE PARTICLE
    # --------------------------------------------------------

    pv_type_index = clamp_round(
        x[0], 0, len(PV_OPTIONS) - 1
    )

    pv_count = clamp_round(
        x[1], 0, SYSTEM["max_pv_panels"]
    )

    wind_type_index = clamp_round(
        x[2], 0, len(WIND_OPTIONS) - 1
    )

    wind_count = clamp_round(
        x[3], 0, SYSTEM["max_wind_turbines"]
    )

    battery_type_index = clamp_round(
        x[4], 0, len(BATTERY_OPTIONS) - 1
    )

    battery_count = clamp_round(
        x[5], 0, SYSTEM["max_batteries"]
    )

    pv = PV_OPTIONS[pv_type_index]
    wind_turbine = WIND_OPTIONS[wind_type_index]
    battery = BATTERY_OPTIONS[battery_type_index]

    solar = weather["solar_irradiance"]
    wind = weather["wind_speed"]

    n = min(len(solar), len(wind))

    if n == 0:
        raise RuntimeError(
            "No valid weather data available."
        )

    load = build_load_profile(
        monthly_kwh,
        n,
    )

    # ========================================================
    # COMPONENT SIZES
    # ========================================================

    pv_kw_each = pv["rated_w"] / 1000.0

    total_pv_kw = (
        pv_count * pv_kw_each
    )

    total_wind_kw = (
        wind_count * wind_turbine["rated_kw"]
    )

    battery_capacity = (
        battery_count * battery["usable_kwh"]
    )

    min_soc = (
        battery_capacity * battery["minimum_soc"]
    )

    soc = (
        battery_capacity * battery["initial_soc"]
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
        battery["round_trip_efficiency"]
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

        pv_generation = (
            pv_count
            * pv_kw_each
            * (solar[i] / 1000.0)
            * pv["performance_factor"]
        )

        # ----------------------------------------------------
        # WIND GENERATION
        # ----------------------------------------------------

        wind_generation = (
            wind_count
            * wind_power_kw(
                wind[i],
                wind_turbine,
            )
        )

        renewable = max(
            0.0,
            pv_generation + wind_generation,
        )

        demand = max(
            0.0,
            load[i],
        )

        total_load += demand
        renewable_generated += renewable

        # ----------------------------------------------------
        # RENEWABLE → LOAD
        # ----------------------------------------------------

        served_direct = min(
            renewable,
            demand,
        )

        renewable_direct += (
            served_direct
        )

        deficit = (
            demand - served_direct
        )

        surplus = (
            renewable - served_direct
        )

        # ----------------------------------------------------
        # RENEWABLE → BATTERY
        # ----------------------------------------------------

        if (
            battery_capacity > 0
            and surplus > 0
        ):

            available_capacity = (
                battery_capacity - soc
            )

            charge = min(
                surplus,
                max(
                    0.0,
                    available_capacity / sqrt_eff,
                ),
            )

            soc = min(
                battery_capacity,
                soc + charge * sqrt_eff,
            )

            renewable_to_battery += charge
            surplus -= charge

        # ----------------------------------------------------
        # CURTAILMENT
        # ----------------------------------------------------

        curtailed += max(
            0.0,
            surplus,
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
                soc - min_soc,
            )

            discharge = min(
                deficit,
                available * sqrt_eff,
            )

            soc = max(
                min_soc,
                soc - discharge / sqrt_eff,
            )

            battery_to_load += discharge
            deficit -= discharge

        # ----------------------------------------------------
        # GRID → LOAD
        # ----------------------------------------------------

        if deficit > 0:
            grid += deficit

        # ----------------------------------------------------
        # SAMPLE FOR CHART
        # ----------------------------------------------------

        sample.append({
            "load": demand,

            "renewable": renewable,

            "grid": max(
                0.0,
                deficit,
            ),

            "soc": (
                soc / battery_capacity * 100.0
                if battery_capacity > 0
                else 0.0
            ),
        })

    # ========================================================
    # ENERGY BALANCE
    # ========================================================

    renewable_served = (
        renewable_direct + battery_to_load
    )

    renewable_fraction = (
        renewable_served / total_load
        if total_load > 0
        else 0.0
    )

    grid_share = (
        grid / total_load
        if total_load > 0
        else 0.0
    )

    # ========================================================
    # TARGET
    # ========================================================

    target_fraction = max(
        0.0,
        min(
            1.0,
            float(
                target_renewable_fraction
            ),
        ),
    )

    target_energy = (
        total_load * target_fraction
    )

    renewable_shortfall = max(
        0.0,
        target_energy - renewable_served,
    )

    # ========================================================
    # CAPITAL COST
    # ========================================================

    capital_cost = (
        pv_count * pv["price_sar"]
        + wind_count * wind_turbine["price_sar"]
        + battery_count * battery["price_sar"]
    )

    if pv_count + wind_count > 0:
        capital_cost += (
            SYSTEM["inverter_cost_sar"]
        )

    if (
        pv_count
        + wind_count
        + battery_count
        > 0
    ):
        capital_cost += (
            SYSTEM["balance_of_system_cost_sar"]
        )

    # ========================================================
    # GRID COST
    # ========================================================

    grid_tariff = SYSTEM.get(
        "grid_tariff_sar_per_kwh",
        0.18,
    )

    annual_grid_cost = (
        grid * grid_tariff
    )

    # ========================================================
    # MULTI-CRITERIA OBJECTIVE
    #
    # The optimizer balances:
    #
    # 1. Reliability / no unmet load
    # 2. Renewable target
    # 3. Low capital cost
    # 4. Low grid energy
    # 5. Low renewable curtailment
    # 6. Reasonable system sizing
    #
    # ========================================================

    # --------------------------------------------------------
    # UNMET ENERGY
    # --------------------------------------------------------

    unmet_penalty = (
        1_000_000.0 * unmet
    )

    # --------------------------------------------------------
    # RENEWABLE TARGET
    # --------------------------------------------------------

    target_penalty = (
        500.0 * renewable_shortfall
    )

    # --------------------------------------------------------
    # GRID
    # --------------------------------------------------------

    grid_penalty = (
        annual_grid_cost
    )

    # --------------------------------------------------------
    # CURTAILMENT
    # --------------------------------------------------------

    annual_load_reference = max(
        total_load,
        1.0,
    )

    curtailment_ratio = (
        curtailed / annual_load_reference
    )

    curtailment_penalty = (
        50_000.0 * curtailment_ratio
    )

    # --------------------------------------------------------
    # GENERATION OVERSIZING
    # --------------------------------------------------------

    # Allow some extra generation because renewable energy
    # must be produced at different times from the load.
    allowed_generation = (
        max(
            target_fraction,
            0.90,
        )
        * total_load
        * 1.15
    )

    excess_generation = max(
        0.0,
        renewable_generated - allowed_generation,
    )

    generation_oversize_penalty = (
        3.0 * excess_generation
    )

    # --------------------------------------------------------
    # BATTERY OVERSIZING
    # --------------------------------------------------------

    average_daily_load = (
        total_load / 365.0
    )

    battery_ratio = (
        battery_capacity
        / max(
            average_daily_load,
            1.0,
        )
    )

    battery_excess_days = max(
        0.0,
        battery_ratio - 1.0,
    )

    battery_oversize_penalty = (
        4_000.0 * battery_excess_days
    )

    # --------------------------------------------------------
    # FINAL OBJECTIVE
    # --------------------------------------------------------

    objective = (
        unmet_penalty
        + target_penalty
        + capital_cost
        + grid_penalty
        + curtailment_penalty
        + generation_oversize_penalty
        + battery_oversize_penalty
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

        "renewable_fraction": max(
            0.0,
            min(
                1.0,
                renewable_fraction,
            ),
        ),

        "grid_share": max(
            0.0,
            min(
                1.0,
                grid_share,
            ),
        ),

        "renewable_shortfall":
            renewable_shortfall,

        "curtailment_ratio":
            curtailment_ratio,

        "generation_oversize_penalty":
            generation_oversize_penalty,

        "battery_oversize_penalty":
            battery_oversize_penalty,

        "sample": sample,

        "pv": pv,

        "wind": wind_turbine,

        "battery": battery,

        "pv_type_index":
            pv_type_index,

        "wind_type_index":
            wind_type_index,

        "battery_type_index":
            battery_type_index,

        "pv_count":
            pv_count,

        "wind_count":
            wind_count,

        "battery_count":
            battery_count,
    }


# ============================================================
# LOCAL SEARCH REFINEMENT
# ============================================================

def refine_solution(
    start_x,
    weather,
    monthly_kwh,
    target_renewable_fraction,
    bounds,
):
    """
    Fast local refinement after PSO.

    The refinement avoids the very large search used previously.

    Step 1:
        Compare all combinations of PV, wind and battery types
        while keeping the PSO quantities.

    Step 2:
        Adjust PV, wind and battery quantities independently
        around the PSO solution.

    This keeps execution practical for local PC and Render.
    """

    best_x = start_x[:]

    best_result = simulate(
        best_x,
        weather,
        monthly_kwh,
        target_renewable_fraction,
    )

    # ========================================================
    # STEP 1: COMPONENT TYPE SEARCH
    # ========================================================

    best_type_x = best_x[:]

    best_type_result = best_result

    for pv_type in range(
        len(PV_OPTIONS)
    ):

        for wind_type in range(
            len(WIND_OPTIONS)
        ):

            for battery_type in range(
                len(BATTERY_OPTIONS)
            ):

                candidate = [
                    pv_type,
                    best_x[1],

                    wind_type,
                    best_x[3],

                    battery_type,
                    best_x[5],
                ]

                result = simulate(
                    candidate,
                    weather,
                    monthly_kwh,
                    target_renewable_fraction,
                )

                if (
                    result["objective"]
                    < best_type_result["objective"]
                ):

                    best_type_x = candidate

                    best_type_result = result

    best_x = best_type_x
    best_result = best_type_result

    # ========================================================
    # STEP 2: QUANTITY SEARCH
    # ========================================================

    quantity_positions = [

        # PV quantity
        (
            1,
            SYSTEM["max_pv_panels"],
            3,
        ),

        # Wind quantity
        (
            3,
            SYSTEM["max_wind_turbines"],
            2,
        ),

        # Battery quantity
        (
            5,
            SYSTEM["max_batteries"],
            3,
        ),
    ]

    improved = True

    # Only two passes to keep execution fast.
    for _ in range(2):

        if not improved:
            break

        improved = False

        for (
            position,
            maximum,
            radius,
        ) in quantity_positions:

            current_value = (
                best_x[position]
            )

            candidate_values = range(
                max(
                    0,
                    current_value - radius,
                ),

                min(
                    maximum,
                    current_value + radius,
                ) + 1,
            )

            for quantity in candidate_values:

                candidate = best_x[:]

                candidate[position] = (
                    quantity
                )

                result = simulate(
                    candidate,
                    weather,
                    monthly_kwh,
                    target_renewable_fraction,
                )

                if (
                    result["objective"]
                    < best_result["objective"]
                ):

                    best_x = candidate

                    best_result = result

                    improved = True

    return best_x, best_result


# ============================================================
# PSO OPTIMIZATION
# ============================================================

def optimize_system(
    weather,
    monthly_kwh,
    target_renewable_fraction=0.90,
):
    """
    Mixed-integer / categorical Particle Swarm Optimization.

    Decision variables:

        x[0] = PV type
        x[1] = PV quantity

        x[2] = Wind type
        x[3] = Wind quantity

        x[4] = Battery type
        x[5] = Battery quantity

    After PSO, a bounded local search refines the solution.
    """

    # ========================================================
    # BOUNDS
    # ========================================================

    bounds = [

        # PV TYPE
        (
            0,
            len(PV_OPTIONS) - 1,
        ),

        # PV QUANTITY
        (
            0,
            SYSTEM["max_pv_panels"],
        ),

        # WIND TYPE
        (
            0,
            len(WIND_OPTIONS) - 1,
        ),

        # WIND QUANTITY
        (
            0,
            SYSTEM["max_wind_turbines"],
        ),

        # BATTERY TYPE
        (
            0,
            len(BATTERY_OPTIONS) - 1,
        ),

        # BATTERY QUANTITY
        (
            0,
            SYSTEM["max_batteries"],
        ),
    ]

    rng = random.Random(
        PSO["seed"]
    )

    particles = []

    # ========================================================
    # INITIAL SWARM
    # ========================================================

    for _ in range(
        PSO["particles"]
    ):

        x = [
            rng.randint(
                lo,
                hi,
            )
            for lo, hi in bounds
        ]

        v = [
            rng.uniform(
                -2.5,
                2.5,
            )
            for _ in range(6)
        ]

        result = simulate(
            x,
            weather,
            monthly_kwh,
            target_renewable_fraction,
        )

        particles.append({

            "x": x,

            "v": v,

            "best_x":
                x[:],

            "best_score":
                result["objective"],
        })

    # ========================================================
    # GLOBAL BEST
    # ========================================================

    gbest = min(
        particles,
        key=lambda p:
            p["best_score"],
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

            for j in range(6):

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

                low, high = bounds[j]

                p["x"][j] = (
                    clamp_round(
                        p["x"][j]
                        + p["v"][j],
                        low,
                        high,
                    )
                )

            result = simulate(
                p["x"],
                weather,
                monthly_kwh,
                target_renewable_fraction,
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
    # LOCAL REFINEMENT
    # ========================================================

    global_x, final = (
        refine_solution(
            global_x,
            weather,
            monthly_kwh,
            target_renewable_fraction,
            bounds,
        )
    )

    # ========================================================
    # SELECTED COMPONENTS
    # ========================================================

    selected_pv = (
        PV_OPTIONS[
            final["pv_type_index"]
        ]
    )

    selected_wind = (
        WIND_OPTIONS[
            final["wind_type_index"]
        ]
    )

    selected_battery = (
        BATTERY_OPTIONS[
            final["battery_type_index"]
        ]
    )

    pv_count = (
        final["pv_count"]
    )

    wind_count = (
        final["wind_count"]
    )

    battery_count = (
        final["battery_count"]
    )

    # ========================================================
    # WEATHER
    # ========================================================

    solar_values = (
        weather["solar_irradiance"]
    )

    wind_values = (
        weather["wind_speed"]
    )

    avg_solar = (
        sum(solar_values)
        / len(solar_values)
        if solar_values
        else 0.0
    )

    avg_wind = (
        sum(wind_values)
        / len(wind_values)
        if wind_values
        else 0.0
    )

    # ========================================================
    # PERFORMANCE
    # ========================================================

    renewable_fraction_pct = (
        final["renewable_fraction"]
        * 100.0
    )

    grid_share_pct = (
        final["grid_share"]
        * 100.0
    )

    # ========================================================
    # PV ENERGY
    # ========================================================

    solar_generated_kwh = (

        pv_count

        * selected_pv["rated_w"]
        / 1000.0

        * (
            sum(solar_values)
            / 1000.0
        )

        * selected_pv[
            "performance_factor"
        ]
    )

    # ========================================================
    # WIND ENERGY
    # ========================================================

    wind_generated_kwh = 0.0

    for v in wind_values:

        wind_generated_kwh += (

            wind_count

            * wind_power_kw(
                v,
                selected_wind,
            )
        )

    # ========================================================
    # BATTERY DETAILS
    # ========================================================

    battery_unit_kwh = (
        selected_battery[
            "usable_kwh"
        ]
    )

    total_battery_kwh = (
        battery_count
        * battery_unit_kwh
    )

    usable_battery_kwh = (
        total_battery_kwh
        * (
            1.0
            - selected_battery[
                "minimum_soc"
            ]
        )
    )

    # ========================================================
    # AVERAGE 24-HOUR PROFILE
    # ========================================================

    sample = final["sample"]

    hourly_profile = []

    for hour in range(24):

        points = (
            sample[hour::24]
        )

        if points:

            avg_load = (
                sum(
                    p["load"]
                    for p in points
                )
                / len(points)
            )

            avg_renewable = (
                sum(
                    p["renewable"]
                    for p in points
                )
                / len(points)
            )

            avg_grid = (
                sum(
                    p["grid"]
                    for p in points
                )
                / len(points)
            )

            avg_soc = (
                sum(
                    p["soc"]
                    for p in points
                )
                / len(points)
            )

        else:

            avg_load = 0.0
            avg_renewable = 0.0
            avg_grid = 0.0
            avg_soc = 0.0

        hourly_profile.append({

            "load":
                avg_load,

            "renewable":
                avg_renewable,

            "grid":
                avg_grid,

            "soc":
                avg_soc,
        })

    # ========================================================
    # SYSTEM TYPE
    # ========================================================

    if (
        pv_count > 0
        and wind_count > 0
        and battery_count > 0
    ):

        system_type = (
            "PV + Wind + Battery"
        )

    elif (
        pv_count > 0
        and battery_count > 0
    ):

        system_type = (
            "PV + Battery"
        )

    elif (
        wind_count > 0
        and battery_count > 0
    ):

        system_type = (
            "Wind + Battery"
        )

    elif (
        pv_count > 0
        and wind_count > 0
    ):

        system_type = (
            "PV + Wind"
        )

    elif pv_count > 0:

        system_type = "PV"

    elif wind_count > 0:

        system_type = "Wind"

    elif battery_count > 0:

        system_type = "Battery"

    else:

        system_type = "Grid Only"

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        # ----------------------------------------------------
        # RECOMMENDED SYSTEM
        # ----------------------------------------------------

        "recommended": {

            "pv_type":
                selected_pv["id"],

            "pv_panels":
                pv_count,

            "pv_panel_w":
                selected_pv["rated_w"],

            "pv_kw":
                round(
                    pv_count
                    * selected_pv["rated_w"]
                    / 1000.0,
                    2,
                ),

            "wind_type":
                selected_wind["id"],

            "wind_turbines":
                wind_count,

            "wind_turbine_kw":
                selected_wind["rated_kw"],

            "wind_kw":
                round(
                    wind_count
                    * selected_wind[
                        "rated_kw"
                    ],
                    2,
                ),

            "battery_type":
                selected_battery["id"],

            "battery_units":
                battery_count,

            "battery_unit_kwh":
                round(
                    battery_unit_kwh,
                    2,
                ),

            "battery_kwh":
                round(
                    total_battery_kwh,
                    2,
                ),

            "battery_usable_kwh":
                round(
                    usable_battery_kwh,
                    2,
                ),

            "system_type":
                system_type,
        },

        # ----------------------------------------------------
        # ECONOMICS
        # ----------------------------------------------------

        "economics": {

            "capital_cost_sar":
                round(
                    final["capital_cost"],
                    0,
                ),

            "annual_grid_energy_kwh":
                round(
                    final["grid"],
                    0,
                ),

            "annual_unserved_kwh":
                round(
                    final["unmet"],
                    0,
                ),

            "curtailed_kwh":
                round(
                    final["curtailed"],
                    0,
                ),

            "estimated_annual_grid_cost_sar":
                round(
                    final["annual_grid_cost"],
                    0,
                ),
        },

        # ----------------------------------------------------
        # PERFORMANCE
        # ----------------------------------------------------

        "performance": {

            "renewable_fraction_pct":
                round(
                    renewable_fraction_pct,
                    1,
                ),

            "grid_share_pct":
                round(
                    max(
                        0.0,
                        grid_share_pct,
                    ),
                    1,
                ),

            "solar_generated_kwh":
                round(
                    solar_generated_kwh,
                    0,
                ),

            "wind_generated_kwh":
                round(
                    wind_generated_kwh,
                    0,
                ),

            "renewable_generated_kwh":
                round(
                    final[
                        "renewable_generated"
                    ],
                    0,
                ),

            "renewable_served_kwh":
                round(
                    final[
                        "renewable_served"
                    ],
                    0,
                ),

            "renewable_target_pct":
                round(
                    target_fraction_for_display(
                        target_renewable_fraction
                    ),
                    1,
                ),
        },

        # ----------------------------------------------------
        # WEATHER
        # ----------------------------------------------------

        "weather": {

            "year":
                weather["year"],

            "valid_hours":
                weather["hours"],

            "average_solar":
                round(
                    avg_solar,
                    3,
                ),

            "average_wind_mps":
                round(
                    avg_wind,
                    3,
                ),
        },

        # ----------------------------------------------------
        # CHART
        # ----------------------------------------------------

        "chart": {

            "hours":
                list(range(24)),

            "load": [
                round(
                    item["load"],
                    3,
                )
                for item in hourly_profile
            ],

            "renewable": [
                round(
                    item["renewable"],
                    3,
                )
                for item in hourly_profile
            ],

            "grid": [
                round(
                    item["grid"],
                    3,
                )
                for item in hourly_profile
            ],
        },

        # ----------------------------------------------------
        # ASSUMPTIONS
        # ----------------------------------------------------

        "assumptions": {

            "pv_w":
                selected_pv["rated_w"],

            "pv_price_sar":
                selected_pv["price_sar"],

            "wind_kw":
                selected_wind["rated_kw"],

            "wind_price_sar":
                selected_wind["price_sar"],

            "battery_kwh":
                selected_battery[
                    "usable_kwh"
                ],

            "battery_price_sar":
                selected_battery[
                    "price_sar"
                ],

            "battery_efficiency_pct":
                selected_battery[
                    "round_trip_efficiency"
                ]
                * 100.0,

            "target_renewable_pct":
                target_renewable_fraction
                * 100.0,
        },

        # ----------------------------------------------------
        # OPTIMIZATION DETAILS
        # ----------------------------------------------------

        "optimization": {

            "objective":
                round(
                    final["objective"],
                    2,
                ),

            "pv_options":
                len(PV_OPTIONS),

            "wind_options":
                len(WIND_OPTIONS),

            "battery_options":
                len(BATTERY_OPTIONS),

            "total_possible_component_types":
                (
                    len(PV_OPTIONS)
                    * len(WIND_OPTIONS)
                    * len(BATTERY_OPTIONS)
                ),

            "method":
                "PSO + Local Search Refinement",

            "objective_design":
                (
                    "Cost + Grid + Target + "
                    "Curtailment + Generation Oversizing "
                    "+ Battery Oversizing"
                ),
        },
    }


# ============================================================
# TARGET DISPLAY
# ============================================================

def target_fraction_for_display(value):
    """
    Convert target fraction to percentage.

    Example:
        0.90 -> 90.0
        1.00 -> 100.0
    """

    return (
        max(
            0.0,
            min(
                1.0,
                float(value),
            ),
        )
        * 100.0
    )