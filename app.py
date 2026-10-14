"""RE-SIZER Flask application: page + JSON API.

    GET  /                page
    GET  /api/elevation   site elevation for a clicked point
    POST /api/analyze     weather from NASA POWER + optimization
"""

import logging
import math
import mimetypes
import os
from datetime import date

import requests
from flask import Flask, jsonify, render_template, request

from config import (
    APP_VERSION,
    BATTERY_OPTIONS,
    PV_OPTIONS,
    SELECTED,
    SYSTEM,
    WIND_OPTIONS,
)
from elevation import get_elevation
from nasa_power import get_nasa_hourly
from optimizer import optimize_system
from optimizer.components import selected_components


# Windows may map .js to text/plain in its registry, and browsers refuse to run
# ES modules with that type. Make sure Flask always sends the right one.
mimetypes.add_type("text/javascript", ".js")

app = Flask(__name__)
log = logging.getLogger(__name__)

NASA_FIRST_YEAR = 2001
# Only COMPLETE years are allowed: loads are annual, so a partial year (e.g.
# the current one) would give wrong annual numbers.
LAST_FULL_YEAR = date.today().year - 1
DEFAULT_YEAR = LAST_FULL_YEAR

MIN_ELEVATION_M = -430
MAX_ELEVATION_M = 8850
HOURS_IN_YEAR = (8760, 8784)


# ============================================================
# MESSAGES (Arabic / English)
# ============================================================

MESSAGES = {
    "ar": {
        "no_location": "حدد موقع المنزل من الخريطة أولًا.",
        "bad_coordinates": "إحداثيات الموقع غير صحيحة.",
        "bad_target": "نسبة الاعتماد على الطاقة المتجددة يجب أن تكون بين 1% و100%.",
        "bad_months": "أدخل 12 قيمة شهرية (أرقام صحيحة وغير سالبة) وواحدة منها على الأقل أكبر من صفر.",
        "file_length": "عدد القيم في الملف ({count}) غير صحيح. المطلوب 8760 قيمة (أو 8784 في السنة الكبيسة)، قيمة لكل ساعة.",
        "file_values": "الملف يحتوي قيمًا غير صالحة (سالبة أو غير رقمية) أو مجموعها صفر.",
        "file_align": "تعذّر مطابقة ساعات الملف مع بيانات NASA.",
        "bad_mode": "طريقة إدخال الاستهلاك غير معروفة.",
        "bad_year": "سنة بيانات NASA يجب أن تكون سنة كاملة بين {first} و{last}.",
        "bad_pv_factor": "معامل أداء الألواح يجب أن يكون بين 0.30 و1.00.",
        "bad_battery_eff": "كفاءة البطارية يجب أن تكون بين 0.50 و1.00.",
        "bad_elevation_number": "ارتفاع الموقع يجب أن يكون رقمًا (بالمتر).",
        "bad_elevation_range": "ارتفاع الموقع خارج المدى المعقول ({low} إلى {high} م).",
        "nasa_failed": "تعذّر الحصول على بيانات NASA POWER لهذا الموقع. حاول مرة أخرى بعد قليل أو اختر موقعًا مختلفًا.",
        "unexpected": "حدث خطأ غير متوقع: {detail}",
    },
    "en": {
        "no_location": "Select the house location on the map first.",
        "bad_coordinates": "The location coordinates are not valid.",
        "bad_target": "The renewable target must be between 1% and 100%.",
        "bad_months": "Enter 12 monthly values (valid, non-negative numbers) and at least one greater than zero.",
        "file_length": "The number of values in the file ({count}) is not valid. 8760 values are required (8784 in a leap year), one per hour.",
        "file_values": "The file contains invalid values (negative or not numbers) or its total is zero.",
        "file_align": "The hours of the file could not be matched with the NASA data.",
        "bad_mode": "Unknown consumption input method.",
        "bad_year": "The NASA data year must be a complete year between {first} and {last}.",
        "bad_pv_factor": "The PV performance factor must be between 0.30 and 1.00.",
        "bad_battery_eff": "The battery efficiency must be between 0.50 and 1.00.",
        "bad_elevation_number": "The site elevation must be a number (metres).",
        "bad_elevation_range": "The site elevation is outside the reasonable range ({low} to {high} m).",
        "nasa_failed": "Could not get NASA POWER data for this location. Try again shortly or choose another location.",
        "unexpected": "An unexpected error occurred: {detail}",
    },
}


class InputError(ValueError):
    """Bad user input. `key` selects the localized message."""

    def __init__(self, key, **params):
        super().__init__(key)
        self.key = key
        self.params = params


def _message(lang, key, **params):
    table = MESSAGES.get(lang, MESSAGES["ar"])
    return table[key].format(**params)


def _lang(payload):
    lang = (payload or {}).get("lang")
    return lang if lang in MESSAGES else "ar"


# ============================================================
# INPUT PARSING / VALIDATION
# ============================================================

def _float(payload, key, error_key):
    try:
        value = float(payload[key])
    except (KeyError, TypeError, ValueError):
        raise InputError(error_key) from None

    if not math.isfinite(value):
        raise InputError(error_key)
    return value


def _number_list(values):
    """list of finite, non-negative floats (or None if anything is wrong)."""
    if not isinstance(values, list):
        return None
    try:
        numbers = [float(v) for v in values]
    except (TypeError, ValueError):
        return None
    if any((not math.isfinite(v)) or v < 0 for v in numbers):
        return None
    return numbers


def _parse_load(payload):
    """-> (load_spec, method dict)"""
    mode = payload.get("input_mode", "monthly")

    if mode == "monthly":
        values = _number_list(payload.get("monthly_values"))
        if values is None or len(values) != 12 or sum(values) <= 0:
            raise InputError("bad_months")

        return (
            {"type": "monthly", "monthly_kwh": values},
            {"code": "monthly_kwh"},
        )

    if mode == "file":
        raw = payload.get("hourly_kwh")
        count = len(raw) if isinstance(raw, list) else 0
        if count not in HOURS_IN_YEAR:
            raise InputError("file_length", count=count)

        values = _number_list(raw)
        if values is None or sum(values) <= 0:
            raise InputError("file_values")

        return {"type": "file", "values": values}, {"code": "hourly_file"}

    raise InputError("bad_mode")


def _elevation(raw):
    """None when empty, a float when valid, InputError otherwise."""
    if raw in (None, ""):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise InputError("bad_elevation_number") from None
    if not (MIN_ELEVATION_M <= value <= MAX_ELEVATION_M):
        raise InputError(
            "bad_elevation_range", low=MIN_ELEVATION_M, high=MAX_ELEVATION_M
        )
    return value


def parse_request(payload):
    """Validate the JSON sent by the browser and return clean values."""
    payload = payload or {}

    # --- location -------------------------------------------
    lat = _float(payload, "lat", "no_location")
    lon = _float(payload, "lon", "no_location")

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise InputError("bad_coordinates")

    # --- renewable target -----------------------------------
    try:
        target = float(payload.get("target_renewable_fraction", 0.90))
    except (TypeError, ValueError):
        raise InputError("bad_target") from None
    if not (0.0 < target <= 1.0):
        raise InputError("bad_target")

    # --- consumption ----------------------------------------
    load_spec, load_method = _parse_load(payload)

    # --- NASA year ------------------------------------------
    try:
        year = int(payload.get("year", DEFAULT_YEAR))
    except (TypeError, ValueError):
        year = 0
    if not (NASA_FIRST_YEAR <= year <= LAST_FULL_YEAR):
        raise InputError("bad_year", first=NASA_FIRST_YEAR, last=LAST_FULL_YEAR)

    # --- optional elevation typed by the user ---------------
    elevation_m = _elevation(payload.get("elevation_m"))

    # --- elevation the page already looked up for the clicked point ---
    try:
        elevation_hint_m = _elevation(payload.get("elevation_hint_m"))
    except InputError:
        elevation_hint_m = None  # a bad hint is simply ignored

    # --- optional equipment settings from the form -----------
    overrides = {}
    for key, low, error in (
        ("pv_performance_factor", 0.30, "bad_pv_factor"),
        ("battery_efficiency", 0.50, "bad_battery_eff"),
    ):
        raw_value = payload.get(key)
        if raw_value in (None, ""):
            continue
        try:
            number = float(raw_value)
        except (TypeError, ValueError):
            raise InputError(error) from None
        if not (low <= number <= 1.0):
            raise InputError(error)
        overrides[key] = number

    return {
        "lat": lat,
        "lon": lon,
        "overrides": overrides,
        "target": target,
        "load_spec": load_spec,
        "load_method": load_method,
        "year": year,
        "elevation_m": elevation_m,
        "elevation_hint_m": elevation_hint_m,
    }


# ============================================================
# ELEVATION  (user  >  DEM  >  NASA grid  >  sea level)
# ============================================================

def resolve_elevation(params):
    """-> (elevation_m or None, source). None = let NASA's value be used."""
    if params["elevation_m"] is not None:          # typed by the user
        return params["elevation_m"], "user"

    if params["elevation_hint_m"] is not None:     # looked up by the page
        return params["elevation_hint_m"], "DEM"

    dem = get_elevation(params["lat"], params["lon"])
    if dem is not None:
        return dem, "DEM"

    return None, "NASA"


# ============================================================
# RESPONSE
# ============================================================

def build_response(params, result):
    site = result["site"]

    load = dict(site["load"])
    load["method"] = params["load_method"]

    return {
        "version": APP_VERSION,
        "location": {"lat": params["lat"], "lon": params["lon"]},
        "target": {"renewable_fraction_pct": round(params["target"] * 100.0, 1)},

        "load": load,
        "weather": site["weather"],
        "comparison": site["comparison"],
        "assumptions": site["assumptions"],
        "optimization": site["optimization"],

        "scenarios": result["scenarios"],
        "recommended_id": result["recommended_id"],

        # maximum quantities the optimizer may use (config.SYSTEM)
        "limits": {
            "pv": SYSTEM["max_pv_panels"],
            "wind": SYSTEM["max_wind_turbines"],
            "battery": SYSTEM["max_batteries"],
        },

        "catalogue": {
            "selected": SELECTED,
            "pv": PV_OPTIONS,
            "wind": WIND_OPTIONS,
            "battery": BATTERY_OPTIONS,
        },
    }


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def home():
    defaults = selected_components()
    return render_template(
        "index.html",
        version=APP_VERSION,
        default_pv_factor=defaults["pv"]["performance_factor"],
        default_battery_eff=defaults["battery"]["round_trip_efficiency"],
        default_target_pct=round(SYSTEM["target_renewable_fraction"] * 100),
        default_year=DEFAULT_YEAR,
        first_year=NASA_FIRST_YEAR,
        last_year=LAST_FULL_YEAR,
    )


@app.get("/api/elevation")
def elevation():
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "bad_coordinates"}), 400

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"error": "bad_coordinates"}), 400

    value = get_elevation(lat, lon)
    if value is None:
        return jsonify({"elevation_m": None, "source": None})

    return jsonify({"elevation_m": round(value, 0), "source": "DEM"})


@app.post("/api/analyze")
def analyze():
    payload = request.get_json(force=True, silent=True) or {}
    lang = _lang(payload)

    try:
        params = parse_request(payload)

        weather = get_nasa_hourly(
            params["lat"], params["lon"], params["year"]
        )

        elevation_m, elevation_source = resolve_elevation(params)

        try:
            result = optimize_system(
                weather,
                params["load_spec"],
                params["target"],
                elevation_m=elevation_m,
                elevation_source=elevation_source,
                overrides=params["overrides"],
            )
        except ValueError as exc:
            if str(exc) == "file_length":
                raise InputError("file_align") from None
            raise

        return jsonify(build_response(params, result))

    except InputError as exc:
        return jsonify({"error": _message(lang, exc.key, **exc.params)}), 400

    except (requests.RequestException, RuntimeError) as exc:
        log.exception("NASA POWER request failed")
        return jsonify({
            "error": _message(lang, "nasa_failed"),
            "details": str(exc),
        }), 502

    except Exception as exc:
        log.exception("Unexpected error in /api/analyze")
        return jsonify({"error": _message(lang, "unexpected", detail=exc)}), 500


# ============================================================
# RUN LOCALLY  (production uses gunicorn, see render.yaml)
# ============================================================

if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
