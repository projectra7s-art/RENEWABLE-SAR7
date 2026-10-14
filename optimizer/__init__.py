"""Sizing optimizer package.

    components.py  PV / wind / load physical models, selected equipment
    economics.py   capital cost and annualization (CRF)
    site.py        weather + load -> hourly per-unit outputs (built once)
    simulation.py  hourly dispatch, cost and objective of one candidate
    pso.py         Particle Swarm Optimization + local refinement, one
                   search per scenario
    report.py      builds the result dicts shown in the UI

Public API:
    optimize_system(weather, load_spec, target_renewable_fraction,
                    elevation_m=None, elevation_source="user",
                    overrides=None)
returns {"site": {...}, "scenarios": [...], "recommended_id": "..."}
"""

from .pso import run_scenarios
from .report import build_scenario_report, build_site_report
from .simulation import simulate
from .site import build_site


def optimize_system(
    weather,
    load_spec,
    target_renewable_fraction=0.90,
    elevation_m=None,
    elevation_source="user",
    overrides=None,
):
    site = build_site(
        weather, load_spec, elevation_m, elevation_source, overrides
    )

    scenarios = []
    for scenario_id, label, x in run_scenarios(site, target_renewable_fraction):
        # keep the per-hour data: it feeds the daily chart
        final = simulate(
            x, site, target_renewable_fraction, record_sample=True
        )
        report = build_scenario_report(
            final, site, target_renewable_fraction
        )
        report["id"] = scenario_id
        report["label"] = label
        scenarios.append(report)

    # The cheapest scenario (lowest objective) is the recommended one, but
    # all of them are returned so the user can choose.
    reaching_target = [
        item for item in scenarios if item["performance"]["target_met"]
    ]
    recommended = min(
        reaching_target or scenarios, key=lambda item: item["objective"]
    )
    for item in scenarios:
        item["cheapest"] = item["id"] == recommended["id"]

    return {
        "site": build_site_report(
            site, target_renewable_fraction, weather["year"]
        ),
        "scenarios": scenarios,
        "recommended_id": recommended["id"],
    }


__all__ = ["optimize_system"]
