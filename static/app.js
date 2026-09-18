let mode = "kwh";
let marker = null;
let selected = { lat: null, lon: null };
let energyChart = null;

const map = L.map("map").setView([20, 0], 2);

L.tileLayer(
  "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
  }
).addTo(map);


// =================================================
// Location selection
// =================================================

function selectLocation(lat, lon) {

  // Convert coordinates to valid numbers
  lat = Number(lat);
  lon = Number(lon);

  // Keep latitude within the valid geographic range
  lat = Math.max(-90, Math.min(90, lat));

  // Normalize longitude to the valid range: -180 ... 180
  lon = ((lon + 180) % 360 + 360) % 360 - 180;

  selected.lat = lat;
  selected.lon = lon;

  document.getElementById("latText").textContent =
    lat.toFixed(6);

  document.getElementById("lonText").textContent =
    lon.toFixed(6);

  if (marker) {
    map.removeLayer(marker);
  }

  marker = L.marker([lat, lon]).addTo(map);
}


map.on("click", (event) => {

  selectLocation(
    event.latlng.lat,
    event.latlng.lng
  );

});


// =================================================
// Input mode tabs
// =================================================

document.querySelectorAll(".tab").forEach((button) => {

  button.addEventListener("click", () => {

    document
      .querySelectorAll(".tab")
      .forEach((b) => b.classList.remove("active"));

    button.classList.add("active");

    mode = button.dataset.mode;

    if (mode === "kwh") {

      document
        .getElementById("kwhFields")
        .classList.remove("hidden");

      document
        .getElementById("billFields")
        .classList.add("hidden");

    } else {

      document
        .getElementById("kwhFields")
        .classList.add("hidden");

      document
        .getElementById("billFields")
        .classList.remove("hidden");

    }

  });

});


// =================================================
// Show / Hide helpers
// =================================================

function show(id) {

  document
    .getElementById(id)
    .classList.remove("hidden");

}


function hide(id) {

  document
    .getElementById(id)
    .classList.add("hidden");

}


function setText(id, value) {

  document
    .getElementById(id)
    .textContent = value;

}


function money(x) {

  return Number(x).toLocaleString("en-US") + " SAR";

}


function num(x, decimals = 1) {

  return Number(x).toLocaleString("en-US", {

    maximumFractionDigits: decimals

  });

}


// =================================================
// Run analysis
// =================================================

async function runAnalysis() {

  hide("error");


  // ---------------------------------------------
  // Check location
  // ---------------------------------------------

  if (selected.lat === null) {

    setText(
      "error",
      "حدد موقع المنزل من الخريطة أولًا."
    );

    show("error");

    return;

  }


  // ---------------------------------------------
  // Read basic inputs
  // ---------------------------------------------

  const year =
    Number(
      document.getElementById("year").value
    );


  // ---------------------------------------------
  // Read renewable target
  // ---------------------------------------------

  const targetRenewable =
    Number(
      document.getElementById("targetRenewable").value
    );


  if (
    !targetRenewable ||
    targetRenewable < 1 ||
    targetRenewable > 100
  ) {

    setText(
      "error",
      "أدخل نسبة تغطية بالطاقة المتجددة بين 1% و100%."
    );

    show("error");

    return;

  }


  // ---------------------------------------------
  // Convert percentage to fraction
  // Example: 90% → 0.90
  // ---------------------------------------------

  const targetRenewableFraction =
    targetRenewable / 100;


  // ---------------------------------------------
  // Build API payload
  // ---------------------------------------------

  const payload = {

    lat: selected.lat,

    lon: selected.lon,

    input_mode: mode,

    year: year,

    target_renewable_fraction:
      targetRenewableFraction

  };


  // ---------------------------------------------
  // KWh input
  // ---------------------------------------------

  if (mode === "kwh") {

    payload.monthly_kwh =
      Number(
        document.getElementById("monthlyKwh").value
      );


    if (
      !payload.monthly_kwh ||
      payload.monthly_kwh <= 0
    ) {

      setText(
        "error",
        "أدخل استهلاكًا شهريًا صحيحًا بالكيلوواط ساعة."
      );

      show("error");

      return;

    }

  }


  // ---------------------------------------------
  // Bill input
  // ---------------------------------------------

  else {

    payload.bill_sar =
      Number(
        document.getElementById("billSar").value
      );


    payload.effective_tariff =
      Number(
        document.getElementById("tariff").value
      );


    if (
      !payload.bill_sar ||
      payload.bill_sar <= 0
    ) {

      setText(
        "error",
        "أدخل قيمة فاتورة صحيحة."
      );

      show("error");

      return;

    }


    if (
      !payload.effective_tariff ||
      payload.effective_tariff <= 0
    ) {

      setText(
        "error",
        "أدخل تعرفة فعالة صحيحة."
      );

      show("error");

      return;

    }

  }


  // ---------------------------------------------
  // Start loading
  // ---------------------------------------------

  hide("results");

  show("loading");


  try {

    const response =
      await fetch(
        "/api/analyze",
        {

          method: "POST",

          headers: {

            "Content-Type":
              "application/json"

          },

          body:
            JSON.stringify(payload)

        }
      );


    const data =
      await response.json();


    if (!response.ok) {

      throw new Error(

        data.error ||
        "حدث خطأ أثناء التحليل."

      );

    }


    // ---------------------------------------------
    // System recommendation
    // ---------------------------------------------

    setText(
      "systemType",
      data.recommended.system_type
    );


    setText(
      "pvPanels",
      data.recommended.pv_panels
    );


    setText(
      "pvKw",
      `${data.recommended.pv_kw} kW`
    );


    setText(
      "windTurbines",
      data.recommended.wind_turbines
    );


    setText(
      "windKw",
      `${data.recommended.wind_kw} kW`
    );


    setText(
      "batteryUnits",
      data.recommended.battery_units
    );


    setText(
      "batteryKwh",
      `${data.recommended.battery_kwh} kWh`
    );


    // ---------------------------------------------
    // Renewable coverage
    // ---------------------------------------------

    setText(
      "renewableFraction",
      `${data.performance.renewable_fraction_pct}%`
    );


    // ---------------------------------------------
    // Weather
    // ---------------------------------------------

    setText(
      "validHours",
      num(
        data.weather.valid_hours,
        0
      )
    );


    setText(
      "avgSolar",
      `${data.weather.average_solar}`
    );


    setText(
      "avgWind",
      `${data.weather.average_wind_mps} m/s`
    );


    setText(
      "avgLoad",
      `${data.load.average_kw} kW`
    );


    // ---------------------------------------------
    // Performance
    // ---------------------------------------------

    setText(
      "targetFraction",
      `${data.target.renewable_fraction_pct}%`
    );


    setText(
      "capitalCost",
      money(
        data.economics.capital_cost_sar
      )
    );


    setText(
      "gridEnergy",
      `${num(
        data.economics.annual_grid_energy_kwh,
        0
      )} kWh`
    );


    setText(
      "unserved",
      `${num(
        data.economics.annual_unserved_kwh,
        0
      )} kWh`
    );


    setText(
      "curtailed",
      `${num(
        data.economics.curtailed_kwh,
        0
      )} kWh`
    );


    // ---------------------------------------------
    // Input summary
    // ---------------------------------------------

    document
      .getElementById("inputSummary")
      .innerHTML = `

        <div>

          <span>Latitude</span>

          <b>
            ${data.location.lat.toFixed(6)}
          </b>

        </div>


        <div>

          <span>Longitude</span>

          <b>
            ${data.location.lon.toFixed(6)}
          </b>

        </div>


        <div>

          <span>Monthly load</span>

          <b>
            ${num(data.load.monthly_kwh)} kWh
          </b>

        </div>


        <div>

          <span>Annual load</span>

          <b>
            ${num(data.load.annual_kwh)} kWh
          </b>

        </div>


        <div>

          <span>Input method</span>

          <b>
            ${data.load.method}
          </b>

        </div>


        <div>

          <span>Renewable target</span>

          <b>
            ${data.target.renewable_fraction_pct}%
          </b>

        </div>


        <div>

          <span>NASA year</span>

          <b>
            ${data.weather.year}
          </b>

        </div>

      `;


    // ---------------------------------------------
    // Chart
    // ---------------------------------------------

    renderChart(data.chart);


    // ---------------------------------------------
    // Show results
    // ---------------------------------------------

    hide("loading");

    show("results");


    window.scrollTo({

      top:
        document
          .getElementById("results")
          .offsetTop - 20,

      behavior: "smooth"

    });


  } catch (error) {

    hide("loading");


    setText(
      "error",
      error.message
    );


    show("error");

  }

}


// =================================================
// Chart
// =================================================

function renderChart(chart) {

  const canvas =
    document.getElementById(
      "energyChart"
    );


  if (energyChart) {

    energyChart.destroy();

  }


  energyChart =
    new Chart(

      canvas,

      {

        type: "line",


        data: {

          labels:

            chart.hours.map(

              h => `${h}:00`

            ),


          datasets: [

            {

              label:
                "الحمل (kW)",

              data:
                chart.load,

              tension:
                0.25,

              borderWidth:
                2

            },


            {

              label:
                "الطاقة المتجددة (kW)",

              data:
                chart.renewable,

              tension:
                0.25,

              borderWidth:
                2

            },


            {

              label:
                "الشبكة (kW)",

              data:
                chart.grid,

              tension:
                0.25,

              borderWidth:
                2

            }

          ]

        },


        options: {

          responsive:
            true,


          interaction: {

            mode:
              "index",

            intersect:
              false

          },


          scales: {

            y: {

              beginAtZero:
                true,


              title: {

                display:
                  true,

                text:
                  "kW"

              }

            }

          }

        }

      }

    );

}


// =================================================
// Run button
// =================================================

document
  .getElementById("runBtn")
  .addEventListener(
    "click",
    runAnalysis
  );