"""Integer Particle Swarm Optimization + local refinement.

Decision variables (3) - the equipment models are fixed in config.SELECTED:
    x[0] number of PV panels        0 .. max_pv_panels
    x[1] number of wind turbines    0 .. max_wind_turbines
    x[2] number of batteries        0 .. max_batteries

Every position is rounded to an integer and clamped to its bounds.

The search is run once per scenario (Solar + Battery, Wind + Battery,
Hybrid); every scenario is returned so the user can compare and choose.
"""

import random

from config import PSO, SYSTEM

from .components import clamp_round
from .simulation import capital_of, simulate


DIMENSIONS = 3
INITIAL_VELOCITY = 2.5
PATIENCE = 8  # iterations without improvement before PSO stops

# Local search neighbourhood. PV and wind are moved TOGETHER because a plain
# one-variable search cannot discover that a turbine pays off only when a few
# panels are removed at the same time.
LOCAL_PV_RADIUS = 10
LOCAL_WIND_RADIUS = 3
LOCAL_BATTERY_RADIUS = 3

# smaller window used to look for a smaller system of the same cost
TRIM_PV_RADIUS = 6
TRIM_WIND_RADIUS = 2
TRIM_BATTERY_RADIUS = 2

# id, label, restriction of the search space
SCENARIOS = (
    ("solar_battery", "Solar + Battery", {"wind_max": 0}),
    ("wind_battery", "Wind + Battery", {"pv_max": 0}),
    ("hybrid", "Hybrid (PV + Wind + Battery)", {"pv_min": 1, "wind_min": 1}),
)

def search_bounds(rule=None):
    """Bounds of the 3 variables, optionally restricted by a scenario rule."""
    rule = rule or {}

    pv_max = min(rule.get("pv_max", SYSTEM["max_pv_panels"]), SYSTEM["max_pv_panels"])
    wind_max = min(
        rule.get("wind_max", SYSTEM["max_wind_turbines"]),
        SYSTEM["max_wind_turbines"],
    )

    return [
        (rule.get("pv_min", 0), pv_max),
        (rule.get("wind_min", 0), wind_max),
        (0, SYSTEM["max_batteries"]),
    ]


def _score(x, site, target):
    """Objective value only (no per-hour chart data)."""
    return simulate(x, site, target, record_sample=False)["objective"]


# ------------------------------------------------------------
# Local refinement (after PSO)
# ------------------------------------------------------------

def _window(value, radius, bounds):
    low, high = bounds
    return range(max(low, value - radius), min(high, value + radius) + 1)


def refine_solution(start_x, site, target, bounds):
    """Local search around the PSO solution (two passes).

    1) (PV, wind) are tried together, battery fixed;
    2) the battery quantity is adjusted.
    """
    best_x = start_x[:]
    best_score = _score(best_x, site, target)

    for _ in range(2):
        changed = False

        for pv in _window(best_x[0], LOCAL_PV_RADIUS, bounds[0]):
            for wind in _window(best_x[1], LOCAL_WIND_RADIUS, bounds[1]):
                candidate = [pv, wind, best_x[2]]
                if candidate == best_x:
                    continue
                score = _score(candidate, site, target)
                if score < best_score:
                    best_x, best_score, changed = candidate, score, True

        for battery in _window(best_x[2], LOCAL_BATTERY_RADIUS, bounds[2]):
            candidate = [best_x[0], best_x[1], battery]
            if candidate == best_x:
                continue
            score = _score(candidate, site, target)
            if score < best_score:
                best_x, best_score, changed = candidate, score, True

        if not changed:
            break

    return best_x


# ------------------------------------------------------------
# Smallest system that is (almost) as cheap
# ------------------------------------------------------------

def trim_solution(best_x, site, target, bounds):
    """Prefer the SMALLER system when it costs practically the same.

    Around the optimum the yearly cost is very flat (an extra battery can pay
    for itself and push the renewable share far above the target). Among the
    designs that still reach the target and whose yearly cost is within
    PSO["size_tolerance"] of the best one, the one with the lowest capital
    cost wins, so the result stays close to the requested target instead of
    over-shooting it.
    """
    best = simulate(best_x, site, target, record_sample=False)
    if best["renewable_fraction"] < min(1.0, target) - 1e-9:
        return best_x  # target not reached: nothing to trim

    limit = best["annual_total_cost"] * (1.0 + PSO["size_tolerance"])
    choice, choice_key = best_x, (best["capital_cost"], best["annual_total_cost"])

    for pv in _window(best_x[0], TRIM_PV_RADIUS, bounds[0]):
        for wind in _window(best_x[1], TRIM_WIND_RADIUS, bounds[1]):
            for battery in _window(best_x[2], TRIM_BATTERY_RADIUS, bounds[2]):
                candidate = [pv, wind, battery]

                # only a design with a lower capital cost can win, and that
                # is known without simulating it
                if capital_of(candidate, site) >= choice_key[0]:
                    continue

                result = simulate(candidate, site, target, record_sample=False)

                if result["renewable_fraction"] < min(1.0, target) - 1e-9:
                    continue
                if result["annual_total_cost"] > limit:
                    continue

                choice = candidate
                choice_key = (
                    result["capital_cost"], result["annual_total_cost"]
                )

    return choice


# ------------------------------------------------------------
# PSO
# ------------------------------------------------------------

def run_pso(site, target, bounds, seed):
    """Run PSO inside `bounds`, then refine. Returns the best vector."""
    rng = random.Random(seed)

    # A scenario that fixes one technology has fewer free variables, so a
    # smaller swarm is enough (this keeps the analysis fast).
    free_dimensions = sum(1 for low, high in bounds if high > low)
    scale = 1.0 if free_dimensions >= 3 else 0.6
    swarm_size = max(8, round(PSO["particles"] * scale))
    max_iterations = max(10, round(PSO["iterations"] * scale))

    # --- initial swarm ---------------------------------------
    particles = []
    for _ in range(swarm_size):
        x = [rng.randint(lo, hi) for lo, hi in bounds]
        v = [
            rng.uniform(-INITIAL_VELOCITY, INITIAL_VELOCITY)
            for _ in range(DIMENSIONS)
        ]
        particles.append({
            "x": x,
            "v": v,
            "best_x": x[:],
            "best_score": _score(x, site, target),
        })

    gbest = min(particles, key=lambda p: p["best_score"])
    global_x = gbest["best_x"][:]
    global_score = gbest["best_score"]

    # --- iterations ------------------------------------------
    stalled = 0
    for _ in range(max_iterations):
        previous_best = global_score

        for p in particles:
            for j in range(DIMENSIONS):
                r1 = rng.random()
                r2 = rng.random()

                p["v"][j] = (
                    PSO["inertia"] * p["v"][j]
                    + PSO["cognitive"] * r1 * (p["best_x"][j] - p["x"][j])
                    + PSO["social"] * r2 * (global_x[j] - p["x"][j])
                )

                low, high = bounds[j]
                p["x"][j] = clamp_round(p["x"][j] + p["v"][j], low, high)

            score = _score(p["x"], site, target)

            if score < p["best_score"]:
                p["best_x"] = p["x"][:]
                p["best_score"] = score

                if score < global_score:
                    global_score = score
                    global_x = p["x"][:]

        # stop early when the swarm has not improved for a while
        stalled = stalled + 1 if global_score >= previous_best else 0
        if stalled >= PATIENCE:
            break

    best_x = refine_solution(global_x, site, target, bounds)
    return trim_solution(best_x, site, target, bounds)


# ------------------------------------------------------------
# All searches
# ------------------------------------------------------------

def run_scenarios(site, target):
    """Returns [(id, label, best_x), ...] - one entry per search."""
    results = []

    for index, (scenario_id, label, rule) in enumerate(SCENARIOS):
        bounds = search_bounds(rule)

        if any(low > high for low, high in bounds):
            continue  # impossible with the configured maximum quantities

        # The cost is almost flat along a "valley" (fewer panels + one more
        # battery costs the same), so one swarm can stop on the wrong side of
        # it. Several independent swarms are run and the best design is kept.
        # Restart 0 uses the same seed as before, so the result can only
        # improve.
        best_x, best_score = None, None
        for restart in range(PSO.get("restarts", 1)):
            x = run_pso(site, target, bounds, PSO["seed"] + index + 10 * restart)
            score = _score(x, site, target)
            if best_score is None or score < best_score:
                best_x, best_score = x, score

        results.append((scenario_id, label, best_x))

    return results
