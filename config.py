APP_VERSION = "1.1.0"

# ------------------------------------------------------------
# Editable component catalogue
# ------------------------------------------------------------

PV = {
    "rated_w": 550.0,
    "performance_factor": 0.90,
    "price_sar": 850.0,
}

WIND = {
    "rated_kw": 2.0,
    "price_sar": 7000.0,
    "cut_in_mps": 3.0,
    "rated_mps": 11.0,
    "cut_out_mps": 25.0,
}

BATTERY = {
    "usable_kwh": 10.0,
    "price_sar": 9000.0,
    "round_trip_efficiency": 0.90,
    "minimum_soc": 0.20,
    "initial_soc": 0.60,
}

SYSTEM = {
    "inverter_cost_sar": 3500.0,
    "balance_of_system_cost_sar": 5000.0,

    # Maximum search limits
    "max_pv_panels": 50,
    "max_wind_turbines": 10,
    "max_batteries": 15,

    # Target renewable contribution
    "target_renewable_fraction": 0.90,

    # Electricity price used for annual grid-energy cost
    "grid_tariff_sar_per_kwh": 0.18,
}

PSO = {
    "particles": 30,
    "iterations": 50,
    "inertia": 0.70,
    "cognitive": 1.49,
    "social": 1.49,
    "seed": 42,
}