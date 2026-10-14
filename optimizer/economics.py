"""Capital cost and its annualization."""

from config import ECONOMICS, SYSTEM


def crf(rate: float, years: float) -> float:
    """Capital recovery factor: yearly payment per 1 SAR invested."""
    if rate <= 0:
        return 1.0 / years
    growth = (1.0 + rate) ** years
    return rate * growth / (growth - 1.0)


def inverter_cost(design) -> float:
    """Inverter price: fixed, or sized on the generator power if configured."""
    if design["pv_count"] + design["wind_count"] <= 0:
        return 0.0

    fixed = SYSTEM["inverter_cost_sar"]
    per_kw = SYSTEM.get("inverter_cost_sar_per_kw", 0.0)
    if per_kw <= 0:
        return fixed

    generator_kw = (
        design["pv_count"] * design["pv"]["rated_w"] / 1000.0
        + design["wind_count"] * design["wind"]["rated_kw"]
    )
    return max(fixed, per_kw * generator_kw)


def capital_breakdown(design) -> dict:
    """Capital cost (SAR) by category for a decoded design."""
    pv_count = design["pv_count"]
    wind_count = design["wind_count"]
    battery_count = design["battery_count"]

    inverter = inverter_cost(design)
    bos = (
        SYSTEM["balance_of_system_cost_sar"]
        if pv_count + wind_count + battery_count > 0
        else 0.0
    )

    return {
        "pv": pv_count * design["pv"]["price_sar"],
        "wind": wind_count * design["wind"]["price_sar"],
        "battery": battery_count * design["battery"]["price_sar"],
        "inverter": inverter,
        "bos": bos,
    }


def total_capital(breakdown: dict) -> float:
    total = breakdown["pv"] + breakdown["wind"] + breakdown["battery"]
    total += breakdown["inverter"]
    total += breakdown["bos"]
    return total


def annualized_capital(breakdown: dict) -> float:
    """Sum of every category multiplied by its own CRF (SAR / year)."""
    rate = ECONOMICS["discount_rate"]
    lifetimes = ECONOMICS["lifetime_years"]

    return sum(
        cost * crf(rate, lifetimes[category])
        for category, cost in breakdown.items()
    )


def annual_cost_per_unit(category: str, price_sar: float) -> float:
    """Annualized cost (SAR / year) of ONE unit of a component."""
    return price_sar * crf(
        ECONOMICS["discount_rate"], ECONOMICS["lifetime_years"][category]
    )


def cost_table(design) -> dict:
    """Itemized cost of a design, with the price of ONE unit of each item.

    total   = unit_price x quantity                  (paid once, SAR)
    annual  = total x CRF(discount rate, lifetime)   (equivalent SAR / year)
    """
    rate = ECONOMICS["discount_rate"]
    lifetimes = ECONOMICS["lifetime_years"]
    costs = capital_breakdown(design)

    items = [
        ("pv", design["pv"]["id"], design["pv"]["price_sar"], design["pv_count"]),
        ("wind", design["wind"]["id"], design["wind"]["price_sar"], design["wind_count"]),
        ("battery", design["battery"]["id"], design["battery"]["price_sar"], design["battery_count"]),
        ("inverter", "", costs["inverter"], 1 if costs["inverter"] > 0 else 0),
        ("bos", "", costs["bos"], 1 if costs["bos"] > 0 else 0),
    ]

    rows = []
    for category, model, unit_price, quantity in items:
        if quantity <= 0:
            continue
        total = costs[category]
        factor = crf(rate, lifetimes[category])
        rows.append({
            "category": category,
            "model": model,
            "unit_price_sar": round(unit_price, 0),
            "quantity": quantity,
            "total_sar": round(total, 0),
            "lifetime_years": lifetimes[category],
            "annual_sar": round(total * factor, 0),
        })

    return {
        "rows": rows,
        "capital_total_sar": round(total_capital(costs), 0),
        "annualized_total_sar": round(annualized_capital(costs), 0),
        "discount_rate_pct": round(rate * 100.0, 2),
    }
