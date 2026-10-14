# RE-SIZER — Smart Renewable Energy Sizing

A standalone web application for preliminary residential renewable-energy sizing.

## What the application does

1. User clicks a house location anywhere on the world map (the elevation of the
   point is looked up automatically).
2. NASA POWER is queried for one complete year of hourly solar irradiance, wind
   speed at 10 m (and 50 m), and air temperature.
3. User enters the consumption in one of two ways:
   - **12 monthly values** (in kWh), or
   - an **hourly file** (CSV/TXT with one kWh value per hour).
4. Integer Particle Swarm Optimization (PSO) searches, for each of three
   scenarios (Solar + Battery, Wind + Battery, Hybrid), the number of:
   - PV panels
   - wind turbines
   - battery units
   The equipment models themselves are fixed in `config.py` (`SELECTED`).
5. The three scenarios are shown side by side; the cheapest one that reaches the
   renewable target is recommended, and the user can choose any of them to see
   its details, costs and charts.
6. The interface is available in Arabic and English (button in the top bar).
7. Night / day mode (button in the top bar; remembered, first visit follows the device).
8. Besides the consumption, the form has the target renewable fraction (slider),
   the PV performance factor and the battery round-trip efficiency; a place-name
   search (OpenStreetMap Nominatim, only when Enter is pressed) helps to find the
   location.

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
   Start:  gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app

`$PORT` is provided by Render, and the longer timeout is needed because the
NASA POWER request plus the optimization can take more than gunicorn's default
30 seconds.

## NASA POWER

The backend calls NASA POWER's Hourly Point API for one complete calendar year with:
- ALLSKY_SFC_SW_DWN (solar irradiance, W/m2)
- WS10M (wind speed at 10 m)
- T2M (air temperature at 2 m)  } optional: if NASA rejects them the request is
- WS50M (wind speed at 50 m)    } repeated with the first two only, and the
                                  defaults in `config.py` are used

Site elevation (used for air density): typed by the user > Copernicus DEM
(90 m) through the Open-Meteo Elevation API (free, no key; attribution is shown
in the footer) > the elevation NASA returns with the weather data
(`geometry.coordinates[2]`, a coarse grid average) > sea level.

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

## Deploying on Render (folder layout matters)

`app.py`, `requirements.txt`, `render.yaml`, `templates/`, `static/` and
`optimizer/` must be at the ROOT of the GitHub repository (not inside an extra
wrapper folder). Upload the whole tree, sub-folders included - use Git (VS Code
Source Control) rather than the drag-and-drop page of GitHub, which can skip
folders. Otherwise Render fails with "requirements.txt not found",
"TemplateNotFound" or "No module named optimizer".

If the repository already contains the old `optimizer.py` or `static/app.js`,
delete them: they are replaced by the `optimizer/` package and `static/js/`.

Render settings (if you do not use `render.yaml`):
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT --timeout 120 --workers 1 app:app`
- Root directory: empty (only fill it if the app is inside a sub-folder)

## Model assumptions (all editable in `config.py`)

- **Wind:** NASA gives the speed at 10 m. It is converted to the turbine hub
  height (`hub_height_m`, default 20 m) with the power law
  `v_hub = v10 * (hub/10)^alpha`. `alpha` is computed from the site's own
  WS10M and WS50M (limits in `SITE`), or `default_shear_exponent` if WS50M is
  not available.
- **Air density:** computed hourly from site elevation and NASA air
  temperature; the wind speed is normalized to the reference density
  (IEC 61400-12). High sites such as Abha (> 2000 m) get about 20% less wind
  power than the same wind at sea level.
- **PV:** `rated x G/1000 x temperature factor x performance_factor`. Cell
  temperature comes from NASA T2M and the irradiance (NOCT model), so
  `performance_factor` only contains the other losses (soiling, wiring,
  inverter...).
- **Load:** with 12 monthly values, each month's energy is spread over that
  month's hours with the 24-hour shape in `LOAD_PROFILE` (every monthly total is
  exact). With an hourly file the values are used as they are; hours are matched
  with the NASA hours by date and hour (file starts on 1 January 00:00, in local
  clock time - NASA hours are local solar time, a small offset).
- **Cost:** every component is annualized with its lifetime and the discount
  rate (`ECONOMICS`); the objective compares that yearly cost with the yearly
  grid cost. O&M and battery degradation are not modeled yet.
- **Search:** PSO runs once per scenario (`SCENARIOS` in `optimizer/pso.py`) over
  three integer variables (PV, wind, battery quantities) followed by a local
  search that moves PV and wind together. The hybrid scenario always contains at
  least one panel and one turbine, so it can always be compared.
- **Battery:** `usable_kwh` is the energy the owner can use; the nominal capacity
  is `usable / (1 - minimum_soc)`.
- **Grid:** the system is grid-tied; a shortfall is bought from the grid. Surplus
  is exported at `feed_in_tariff_sar_per_kwh` (0 by default = no revenue).
- **Years:** only complete calendar years are accepted.

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

    app.py                    Flask routes: page, GET /api/elevation, POST /api/analyze
    elevation.py              site elevation (Open-Meteo / Copernicus DEM)
    config.py                 Equipment catalogues, system, objective weights, PSO settings
    nasa_power.py             NASA POWER API integration

    optimizer/
      __init__.py             optimize_system(...)  <- the only function app.py calls
      components.py           PV / wind / load physical models (shear, air density, cell temperature)
      economics.py            capital cost and its annualization (CRF)
      site.py                 weather -> hourly per-unit outputs, built once per analysis
      simulation.py           hourly dispatch, cost and objective of one candidate
      pso.py                  PSO + local refinement (one search per scenario)
      report.py               builds the result dict shown in the UI

    templates/index.html      Arabic/RTL page (data-bind attributes fill the numbers)
    static/style.css          styling (sections: tokens, layout, panels, form, results, responsive)
    static/js/
      main.js                 entry point
      map.js                  Leaflet map + location selection
      form.js                 input tabs + validation
      api.js                  fetch /api/analyze
      results.js              fills the results from the response (data-bind)
      charts.js               Chart.js charts
      i18n.js                 Arabic / English texts (add new sentences to both)
      format.js, ui.js        small helpers

    Dockerfile                container deployment
    render.yaml               Render deployment configuration
    start_windows.bat         Windows setup/run script

## Editing tips

- Change equipment, prices, limits, penalty weights, selected models: `config.py` only.
- Add or change a sentence in the page: `static/js/i18n.js` (both languages).
- Show a new number in the results: add an element with
  `data-bind="section.key"` and optionally `data-fmt="kw|kwh|sar|pct|..."`
  in `templates/index.html` (formats are defined in `static/js/format.js`).
- Run locally with auto-reload: set `FLASK_DEBUG=1` before `python app.py`.


## Cost model (what the numbers mean)

- **Total cost** (shown in the page) = sum of (price of ONE unit x quantity) for
  PV, wind, battery, plus the inverter and the balance of system. Paid once.
- Internally the optimizer compares designs by the **yearly cost** = each item's
  cost x CRF (`CRF = r(1+r)^n / ((1+r)^n - 1)`, `r` = discount rate, `n` = item
  life, see `ECONOMICS` in `config.py`) + the yearly grid bill - export revenue.
  The recommended scenario is the one with the lowest yearly cost that reaches
  the target. The yearly numbers stay in the API response (`economics`, `costs`).
- Wind turbine prices are about 1,500 SAR per kW (turbine only).
- The inverter is a fixed price unless `inverter_cost_sar_per_kw` is set.
- The optimizer picks the design with the lowest yearly cost that reaches the
  target; among designs within `size_tolerance` (1%) of it, the smallest system
  wins, so the result stays close to the requested target.
- Site elevation comes from the map (Open-Meteo / OpenTopoData DEM). NASA's
  temperature is moved from its grid-cell elevation to the site elevation with
  6.5 degC per 1000 m (`SITE["lapse_rate_correction"]`).
- **Temperature switch:** `SITE["use_temperature"]` in `config.py`. `True` uses
  NASA air temperature (PV cell-temperature loss + air density); `False` ignores
  temperature completely (no PV temperature factor, standard-atmosphere air
  density) and the PV performance factor switches automatically to
  `performance_factor_temp_ignored` (0.80) so the temperature loss is still
  counted. The page's "PV Performance Factor" field shows the value in use.
