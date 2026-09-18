APP_VERSION = "2.0.0"

# ------------------------------------------------------------
# PV Catalogue
# ------------------------------------------------------------

PV_OPTIONS = [
    {
        "id": "PV450",
        "rated_w": 450.0,
        "performance_factor": 0.90,
        "price_sar": 550.0,
    },
    {
        "id": "PV550",
        "rated_w": 550.0,
        "performance_factor": 0.90,
        "price_sar": 650.0,
    },
    {
        "id": "PV600",
        "rated_w": 600.0,
        "performance_factor": 0.90,
        "price_sar": 750.0,
    },
    {
        "id": "PV650",
        "rated_w": 650.0,
        "performance_factor": 0.90,
        "price_sar": 850.0,
    },
]


# ------------------------------------------------------------
# Wind Turbine Catalogue
# ------------------------------------------------------------

WIND_OPTIONS = [
    {
        "id": "WIND1",
        "rated_kw": 1.0,
        "price_sar": 3000.0,
        "cut_in_mps": 3.0,
        "rated_mps": 11.0,
        "cut_out_mps": 25.0,
    },
    {
        "id": "WIND2",
        "rated_kw": 2.0,
        "price_sar": 5000.0,
        "cut_in_mps": 3.0,
        "rated_mps": 11.0,
        "cut_out_mps": 25.0,
    },
    {
        "id": "WIND3",
        "rated_kw": 3.0,
        "price_sar": 7000.0,
        "cut_in_mps": 3.0,
        "rated_mps": 11.0,
        "cut_out_mps": 25.0,
    },
    {
        "id": "WIND5",
        "rated_kw": 5.0,
        "price_sar": 11000.0,
        "cut_in_mps": 3.0,
        "rated_mps": 11.0,
        "cut_out_mps": 25.0,
    },
]


# ------------------------------------------------------------
# Battery Catalogue
# ------------------------------------------------------------

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
# System Settings
# ------------------------------------------------------------

SYSTEM = {
    "inverter_cost_sar": 3500.0,
    "balance_of_system_cost_sar": 5000.0,

    # Maximum number of units of each selected technology
    "max_pv_panels": 150,
    "max_wind_turbines": 50,
    "max_batteries": 50,

    # Target renewable contribution
    "target_renewable_fraction": 0.90,

    # Electricity price
    "grid_tariff_sar_per_kwh": 0.18,
}


# ------------------------------------------------------------
# PSO Settings
# ------------------------------------------------------------

PSO = {
    "particles": 12,
    "iterations": 15,
    "inertia": 0.70,
    "cognitive": 1.49,
    "social": 1.49,
    "seed": 42,
}