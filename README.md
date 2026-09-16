# RE-SIZER — Smart Renewable Energy Sizing

A standalone web application for preliminary residential renewable-energy sizing.

## What the application does

1. User clicks a house location on the map.
2. The backend obtains latitude and longitude.
3. NASA POWER is queried for hourly solar irradiance and wind speed.
4. User enters either:
   - monthly electricity consumption in kWh, or
   - monthly bill in SAR + an effective tariff for a rough estimate.
5. The application builds a generic residential hourly load profile.
6. Integer Particle Swarm Optimization (PSO) searches for:
   - number of PV panels
   - number of wind turbines
   - number of battery units
7. A dashboard shows the recommended configuration, costs, renewable fraction,
   grid energy, and a representative 24-hour chart.

## Recommended engineering input

For the most accurate result, enter the **kWh/month printed on the electricity bill**.

The bill-value mode is intentionally an estimate. A currency amount is not a physical
power/energy unit and cannot be converted to Watt with one universal constant.

## Run on Windows

### Option A — one click
Double-click:

    start_windows.bat

### Option B — terminal

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    python app.py

Then open:

    http://127.0.0.1:5000

## Deploy online

The project includes `render.yaml` and a production Gunicorn command.

Typical deployment flow on Render:

1. Create a GitHub repository.
2. Upload this project.
3. Create a new Web Service from the repository.
4. Render can use the included `render.yaml`, or use:
   Build:  pip install -r requirements.txt
   Start:  gunicorn --bind 0.0.0.0:5000 app:app

## NASA POWER

The backend calls NASA POWER's Hourly Point API with:
- ALLSKY_SFC_SW_DWN
- WS10M

NASA POWER:
https://power.larc.nasa.gov/

Official API documentation:
https://power.larc.nasa.gov/docs/services/api/

## Important project assumptions

`config.py` contains editable values for:
- PV panel rating / price / performance factor
- wind turbine rating / price / generic power curve
- battery usable capacity / price / efficiency / SOC
- inverter and balance-of-system cost
- PSO population and iteration settings

Replace these with validated values from the actual equipment used in your study.

## Accuracy note

This is a complete working prototype, but it is not a construction-ready engineering
design. For a final academic or engineering version, improve:
- the hourly residential load profile using real meter data
- Saudi electricity-billing calculation
- PV temperature/tilt/orientation effects
- wind turbine manufacturer's actual power curve
- inverter constraints
- battery degradation
- battery cycle limits
- cable/protection/system constraints
- land/roof-area constraints
- system reliability metrics
- local utility/grid-interconnection requirements

## Files

app.py                    Flask application and API
config.py                 Component + PSO settings
nasa_power.py             NASA POWER API integration
optimizer.py              PSO and energy simulation
templates/index.html      Arabic/RTL web interface
static/app.js             map, API calls and charting
static/style.css          user interface styling
Dockerfile                container deployment
render.yaml               Render deployment configuration
start_windows.bat         Windows setup/run script
