from flask import Flask, render_template, request, jsonify
from nasa_power import get_nasa_hourly
from optimizer import optimize_system
from config import APP_VERSION

app = Flask(__name__)


@app.get("/")
def home():
    return render_template("index.html", version=APP_VERSION)


@app.post("/api/analyze")
def analyze():
    try:
        payload = request.get_json(force=True)

        # ------------------------------------------------------------
        # LOCATION
        # ------------------------------------------------------------
        lat = float(payload["lat"])
        lon = float(payload["lon"])

        # ------------------------------------------------------------
        # INPUT MODE
        # ------------------------------------------------------------
        input_mode = payload.get("input_mode", "bill")

        # ------------------------------------------------------------
        # TARGET RENEWABLE FRACTION
        # User chooses the required renewable contribution.
        # Example:
        # 0.90 = 90%
        # 0.80 = 80%
        # 0.70 = 70%
        # ------------------------------------------------------------
        target_renewable_fraction = float(
            payload.get("target_renewable_fraction", 0.90)
        )

        if not 0.0 < target_renewable_fraction <= 1.0:
            raise ValueError(
                "نسبة الاعتماد على الطاقة المتجددة يجب أن تكون بين 1% و100%."
            )

        # ------------------------------------------------------------
        # LOCATION VALIDATION
        # ------------------------------------------------------------
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("إحداثيات الموقع غير صحيحة.")

        # ------------------------------------------------------------
        # ELECTRICITY CONSUMPTION
        # ------------------------------------------------------------
        if input_mode == "kwh":

            monthly_kwh = float(payload["monthly_kwh"])

            if monthly_kwh <= 0:
                raise ValueError(
                    "أدخل استهلاكًا شهريًا أكبر من صفر."
                )

            bill_sar = None
            bill_method = "Direct kWh input"

        else:

            bill_sar = float(payload["bill_sar"])

            if bill_sar <= 0:
                raise ValueError(
                    "أدخل فاتورة شهرية أكبر من صفر."
                )

            # IMPORTANT:
            # A bill amount cannot be converted to kWh with one universal
            # physical conversion. The prototype uses an editable effective
            # tariff chosen by the user. For final engineering use, direct
            # kWh from the electricity bill is preferred.

            effective_tariff = float(
                payload.get("effective_tariff", 0.18)
            )

            if effective_tariff <= 0:
                raise ValueError(
                    "قيمة التعرفة الفعالة يجب أن تكون أكبر من صفر."
                )

            monthly_kwh = bill_sar / effective_tariff

            bill_method = (
                f"Estimated from bill using "
                f"{effective_tariff:.3f} SAR/kWh"
            )

        # ------------------------------------------------------------
        # YEAR + NASA POWER WEATHER DATA
        # ------------------------------------------------------------
        year = int(payload.get("year", 2025))

        weather = get_nasa_hourly(
            lat,
            lon,
            year
        )

        # ------------------------------------------------------------
        # PSO OPTIMIZATION
        # ------------------------------------------------------------
        result = optimize_system(
            weather,
            monthly_kwh,
            target_renewable_fraction
        )

        # ------------------------------------------------------------
        # AVERAGE LOAD
        # ------------------------------------------------------------
        avg_kw = monthly_kwh / (30.0 * 24.0)

        # ------------------------------------------------------------
        # RESPONSE
        # ------------------------------------------------------------
        return jsonify({

            "version": APP_VERSION,

            "location": {
                "lat": lat,
                "lon": lon
            },

            "load": {
                "monthly_kwh": round(monthly_kwh, 1),

                "annual_kwh": round(
                    monthly_kwh * 12.0,
                    1
                ),

                "average_kw": round(
                    avg_kw,
                    2
                ),

                "bill_sar": (
                    round(bill_sar, 2)
                    if bill_sar is not None
                    else None
                ),

                "method": bill_method
            },

            # --------------------------------------------------------
            # USER TARGET
            # --------------------------------------------------------
            "target": {
                "renewable_fraction_pct": round(
                    target_renewable_fraction * 100.0,
                    1
                )
            },

            # --------------------------------------------------------
            # WEATHER
            # --------------------------------------------------------
            "weather": result["weather"],

            # --------------------------------------------------------
            # RECOMMENDED SYSTEM
            # --------------------------------------------------------
            "recommended": result["recommended"],

            # --------------------------------------------------------
            # ECONOMICS
            # --------------------------------------------------------
            "economics": result["economics"],

            # --------------------------------------------------------
            # PERFORMANCE
            # --------------------------------------------------------
            "performance": result["performance"],

            # --------------------------------------------------------
            # CHART
            # --------------------------------------------------------
            "chart": result["chart"],

            # --------------------------------------------------------
            # ASSUMPTIONS
            # --------------------------------------------------------
            "assumptions": result["assumptions"]
        })

    except Exception as exc:

        return jsonify({
            "error": str(exc)
        }), 400


# ------------------------------------------------------------
# RUN APPLICATION
# ------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )