APP_VERSION = "2.4.7"

# ------------------------------------------------------------
# PV Catalogue
# ------------------------------------------------------------
# performance_factor = losses OTHER than temperature (soiling, wiring,
#                      mismatch, inverter, availability).
# temp_coeff_per_c   = power change per degC of cell temperature (negative).
# noct_c             = nominal operating cell temperature (datasheet).
# Cell temperature is computed hourly from NASA air temperature and the
# irradiance, so the temperature loss is NOT included in performance_factor.
#
# performance_factor_temp_ignored = the factor that is used AUTOMATICALLY when
#     SITE["use_temperature"] is False. Temperature is then not modelled, so
#     this value already contains a typical temperature loss.

PV_OPTIONS = [
    {
        "id": "PV450",
        "rated_w": 450.0,
        "performance_factor": 0.88,
        "performance_factor_temp_ignored": 0.80,
        "temp_coeff_per_c": -0.0035,
        "noct_c": 45.0,
        "price_sar": 550.0,
    },
    {
        "id": "PV550",
        "rated_w": 550.0,
        "performance_factor": 0.88,
        "performance_factor_temp_ignored": 0.80,
        "temp_coeff_per_c": -0.0035,
        "noct_c": 45.0,
        "price_sar": 650.0,
    },
    {
        "id": "PV600",
        "rated_w": 600.0,
        "performance_factor": 0.88,
        "performance_factor_temp_ignored": 0.80,
        "temp_coeff_per_c": -0.0035,
        "noct_c": 45.0,
        "price_sar": 750.0,
    },
    {
        "id": "PV650",
        "rated_w": 650.0,
        "performance_factor": 0.88,
        "performance_factor_temp_ignored": 0.80,
        "temp_coeff_per_c": -0.0035,
        "noct_c": 45.0,
        "price_sar": 850.0,
    },
]


# ------------------------------------------------------------
# Wind Turbine Catalogue
# ------------------------------------------------------------
# hub_height_m: NASA wind is given at 10 m (and 50 m) above ground; the
# speed is converted to this height before the power curve is applied.

# price_sar: price of ONE turbine (about 1,500 SAR per kW: a 2 kW turbine is
# 2,000 - 4,000 SAR). It covers the turbine only; put the tower, foundation and
# installation in SYSTEM["balance_of_system_cost_sar"] if you want them counted.

WIND_OPTIONS = [
    {
        "id": "WIND1",
        "rated_kw": 1.0,
        "price_sar": 1500.0,
        "hub_height_m": 20.0,
        "cut_in_mps": 3.0,
        "rated_mps": 11.0,
        "cut_out_mps": 25.0,
    },
    {
        "id": "WIND2",
        "rated_kw": 2.0,
        "price_sar": 3000.0,
        "hub_height_m": 20.0,
        "cut_in_mps": 3.0,
        "rated_mps": 11.0,
        "cut_out_mps": 25.0,
    },
    {
        "id": "WIND3",
        "rated_kw": 3.0,
        "price_sar": 4500.0,
        "hub_height_m": 20.0,
        "cut_in_mps": 3.0,
        "rated_mps": 11.0,
        "cut_out_mps": 25.0,
    },
    {
        "id": "WIND5",
        "rated_kw": 5.0,
        "price_sar": 7500.0,
        "hub_height_m": 20.0,
        "cut_in_mps": 3.0,
        "rated_mps": 11.0,
        "cut_out_mps": 25.0,
    },
]


# ------------------------------------------------------------
# Battery Catalogue
# ------------------------------------------------------------

# usable_kwh: energy the owner can really use (= difference between the
# maximum and the minimum state of charge). The nominal capacity is therefore
#   nominal = usable_kwh / (1 - minimum_soc)
# so that the SOC window [minimum_soc, 100%] delivers exactly usable_kwh.

BATTERY_OPTIONS = [
    {
        "id": "BAT5",
        "usable_kwh": 5.0,
        "price_sar": 3000.0,
        "round_trip_efficiency": 0.90,
        "minimum_soc": 0.20,
        "initial_soc": 0.60,
    },
    {
        "id": "BAT10",
        "usable_kwh": 10.0,
        "price_sar": 5500.0,
        "round_trip_efficiency": 0.90,
        "minimum_soc": 0.20,
        "initial_soc": 0.60,
    },
    {
        "id": "BAT15",
        "usable_kwh": 15.0,
        "price_sar": 8000.0,
        "round_trip_efficiency": 0.90,
        "minimum_soc": 0.20,
        "initial_soc": 0.60,
    },
    {
        "id": "BAT20",
        "usable_kwh": 20.0,
        "price_sar": 10500.0,
        "round_trip_efficiency": 0.90,
        "minimum_soc": 0.20,
        "initial_soc": 0.60,
    },
]


# ------------------------------------------------------------
# Selected equipment
# ------------------------------------------------------------
# PSO decides only HOW MANY units to buy (x1 = PV panels, x2 = wind
# turbines, x3 = batteries). The equipment model of each technology is fixed
# here by its id from the catalogues above. Change an id to study another
# model; edit a catalogue entry to change its price or rating.

SELECTED = {
    "pv": "PV550",
    "wind": "WIND2",
    "battery": "BAT10",
}


# ------------------------------------------------------------
# System Settings
# ------------------------------------------------------------

SYSTEM = {
    # Inverter: fixed price, or (if the per-kW price below is > 0) the larger
    # of the fixed price and  per_kw x (PV kW + wind kW).  A 20+ kW system needs
    # a bigger inverter than a 3 kW one; a typical string inverter costs about
    # 400 - 500 SAR per kW.
    "inverter_cost_sar": 3500.0,
    "inverter_cost_sar_per_kw": 0.0,
    "balance_of_system_cost_sar": 5000.0,

    # Maximum number of units of each selected technology
    "max_pv_panels": 150,
    "max_wind_turbines": 50,
    "max_batteries": 50,

    # Target renewable contribution
    "target_renewable_fraction": 0.90,

    # Electricity price (SEC residential, first 6000 kWh/month, before VAT)
    "grid_tariff_sar_per_kwh": 0.18,

    # Grid-tied system. Surplus energy that neither the load nor the battery
    # can use is exported. Saudi Arabia does not pay a fixed feed-in price for
    # small rooftop systems in this model, so the default is 0 (= surplus is
    # wasted). Put a positive value to reward exported energy.
    "feed_in_tariff_sar_per_kwh": 0.0,
}


# ------------------------------------------------------------
# Site / Weather Assumptions
# ------------------------------------------------------------
# Wind: v_hub = v10 * (hub_height / 10) ** shear_exponent
#   shear_exponent is computed from NASA WS10M and WS50M when both are
#   available; otherwise default_shear_exponent is used.
# Air density: rho = P(elevation) / (R * T). Wind power is proportional to
#   rho, so high sites (e.g. Abha, > 2000 m) produce less than sea level.
#   The speed is normalized to the reference density before the power curve
#   (IEC 61400-12 method).

SITE = {
    "wind_lower_height_m": 10.0,          # NASA WS10M
    "wind_upper_height_m": 50.0,          # NASA WS50M
    "default_shear_exponent": 0.14,
    "shear_exponent_limits": (0.05, 0.40),

    "apply_air_density": True,
    "reference_air_density": 1.225,       # kg/m3 at sea level, 15 degC

    # TEMPERATURE SWITCH.  True  = use NASA air temperature (PV cell-temperature
    # loss + air density).  False = ignore temperature completely:
    #   - PV output has NO temperature factor (see pv_panel_kw), and
    #   - wind air density uses the standard atmosphere of the site elevation.
    # When it is False the PV performance factor switches AUTOMATICALLY to
    # "performance_factor_temp_ignored" of the PV catalogue (0.80 instead of
    # 0.88), so the temperature loss is not forgotten.
    "use_temperature": True,

    # used when NASA does not return T2M
    "fallback_ambient_c": 25.0,

    # NASA temperature is a model value at the elevation of its grid cell
    # (tens of km wide). When the real site is higher or lower, the air is
    # colder or warmer by about 6.5 degC per 1000 m.
    "lapse_rate_correction": True,
    "lapse_rate_c_per_m": 0.0065,
}


# ------------------------------------------------------------
# Load Profile
# ------------------------------------------------------------
# The user gives EITHER 12 monthly values (kWh) OR an hourly file.
# hourly_shape is used only for the monthly option: it spreads each day's
# energy over the 24 hours (share of the daily energy in each hour,
# normalized). Replace it with a measured shape if you have one.

LOAD_PROFILE = {
    "hourly_shape": [
        0.020, 0.019, 0.018, 0.017, 0.017, 0.020,
        0.024, 0.032, 0.038, 0.040, 0.041, 0.042,
        0.043, 0.044, 0.046, 0.050, 0.058, 0.068,
        0.081, 0.095, 0.090, 0.076, 0.055, 0.031,
    ],
}


# ------------------------------------------------------------
# Economics
# ------------------------------------------------------------
# Every component is annualized with the capital recovery factor
#   CRF = r (1+r)^n / ((1+r)^n - 1)
# so capital cost and yearly grid cost are compared on the same basis.
# Operation & maintenance and battery degradation are not modeled.

ECONOMICS = {
    "discount_rate": 0.05,
    "lifetime_years": {
        "pv": 25,
        "wind": 20,
        "battery": 12,
        "inverter": 12,
        "bos": 25,
    },
}


# ------------------------------------------------------------
# Objective Function Weights  (all in SAR per YEAR)
# ------------------------------------------------------------
# objective = annualized capital + annual grid cost + penalties below.
#
# * renewable_shortfall: large on purpose - the target is a requirement.
# * curtailment: tiny tie-breaker only.
# * generation_oversize / battery_oversize: OFF (0). With an annualized-cost
#   objective, oversizing already costs money, and extra penalties would
#   unfairly favour one technology (wind produces in many hours, so it was
#   penalized more). Raise them only if you want to force smaller systems.

OBJECTIVE = {
    "unmet_penalty_per_kwh": 100_000.0,
    "renewable_shortfall_penalty_per_kwh": 50.0,
    "curtailment_penalty_per_kwh": 0.02,
    "generation_oversize_penalty_per_kwh": 0.0,
    "generation_allowed_margin": 1.15,        # allowed generation / load
    "generation_min_target": 0.90,
    "battery_oversize_penalty_per_day": 0.0,  # per day of storage above 1
}


# ------------------------------------------------------------
# PSO Settings
# ------------------------------------------------------------

PSO = {
    "particles": 20,
    "iterations": 25,
    "inertia": 0.70,
    "cognitive": 1.49,
    "social": 1.49,
    "seed": 42,

    # Number of independent PSO runs per scenario; the best design is kept.
    # 1 = a single run (faster), 3 = recommended (about 2.4 times slower).
    "restarts": 3,

    # A design is "practically as cheap" if its yearly cost is within this
    # fraction of the best one; among those the smallest system is chosen.
    "size_tolerance": 0.01,
}
