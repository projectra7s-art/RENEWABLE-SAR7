// Input form: consumption modes (12 monthly boxes / hourly file), unit
// switch, file reading and building the JSON payload.

import { getLang, t } from "./i18n.js";
import { num } from "./format.js";
import { $, setText } from "./ui.js";

const state = {
  mode: "monthly",     // "monthly" | "file"
  autoElevation: null, // elevation looked up from the map (metres) or null
  hourly: null,        // parsed file values, or null
  hourlyError: null,   // message when the file is not valid
};

const monthInputs = () => [...document.querySelectorAll("[data-month]")];

// ------------------------------------------------------------
// Hourly file
// ------------------------------------------------------------

const NUMBER = /^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/;

// A header cell that names the consumption column ("Load (kW)", "Demand"...).
// Not "kW" alone: "Solar insolation (kW/m2)" must never match.
const LOAD_HEADER = /load|demand|consum|حمل|استهلاك/i;

/** Index of the column whose header names the load, or null. */
function findLoadColumn(lines) {
  for (const line of lines) {
    const cells = line.split(/[;,\t]/).map((cell) => cell.trim());
    if (cells.every((cell) => cell === "" || NUMBER.test(cell))) continue;
    const index = cells.findIndex((cell) => LOAD_HEADER.test(cell));
    return index >= 0 ? index : null;   // first text row = the header
  }
  return null;
}

/**
 * One value per line.
 * - If the header names a load column, that column is used (so a file with
 *   Load + Wind + Solar columns gives the load, not the solar values).
 * - Otherwise, with several columns the LAST numeric one is used.
 */
export function parseHourlyText(text) {
  const values = [];
  const lines = text.split(/\r?\n/);
  const loadColumn = findLoadColumn(lines);

  for (const line of lines) {
    if (loadColumn !== null) {
      const cell = (line.split(/[;,\t]/)[loadColumn] ?? "").trim();
      if (NUMBER.test(cell)) values.push(Number(cell));
      continue;
    }

    const cells = line
      .split(/[;,\t]+/)
      .map((cell) => cell.trim())
      .filter((cell) => cell !== "");

    for (let i = cells.length - 1; i >= 0; i--) {
      if (NUMBER.test(cells[i])) {
        values.push(Number(cells[i]));
        break;
      }
    }
  }

  return values;
}

function showFileStatus() {
  const status = $("fileStatus");
  status.classList.remove("ok", "bad");

  if (state.hourlyError) {
    status.textContent = state.hourlyError;
    status.classList.add("bad");
  } else if (state.hourly) {
    const total = state.hourly.reduce((a, b) => a + b, 0);
    status.textContent = t("file.ok", {
      count: num(state.hourly.length, 0),
      total: num(total, 0),
      avg: num(total / state.hourly.length, 2),
    });
    status.classList.add("ok");
  } else {
    status.textContent = t("file.none");
  }
}

async function onFileChosen(event) {
  const file = event.target.files[0];
  state.hourly = null;
  state.hourlyError = null;

  if (file) {
    try {
      const values = parseHourlyText(await file.text());

      if (values.length === 8760 || values.length === 8784) {
        state.hourly = values;
      } else {
        state.hourlyError = t("file.bad_count", { count: num(values.length, 0) });
      }
    } catch {
      state.hourlyError = t("file.read_error");
    }
  }

  showFileStatus();
}

// ------------------------------------------------------------
// Init
// ------------------------------------------------------------

export function initForm() {
  // mode tabs
  const tabs = document.querySelectorAll(".tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      state.mode = tab.dataset.mode;

      tabs.forEach((other) => {
        const active = other === tab;
        other.classList.toggle("active", active);
        other.setAttribute("aria-selected", String(active));
      });

      $("monthlyFields").classList.toggle("hidden", state.mode !== "monthly");
      $("fileFields").classList.toggle("hidden", state.mode !== "file");
    });
  });

  // fill all 12 months with one value
  $("fillBtn").addEventListener("click", () => {
    const value = $("fillValue").value;
    if (value !== "") monthInputs().forEach((input) => (input.value = value));
  });

  $("hourlyFile").addEventListener("change", onFileChosen);

  // renewable-target slider shows its value
  const slider = $("targetRenewable");
  const showTarget = () => {
    setText("targetValue", `${slider.value}%`);
    // filled part of the track (drawn in style.css)
    const share = (slider.value - slider.min) / (slider.max - slider.min);
    slider.style.setProperty("--fill", `${(share * 100).toFixed(1)}%`);
  };
  slider.addEventListener("input", showTarget);
  showTarget();

  // keep the status line in the current language
  document.addEventListener("languagechange", () => {
    if (state.hourlyError) {
      // the message was built in the old language: rebuild it from the file
      onFileChosen({ target: $("hourlyFile") });
    } else {
      showFileStatus();
    }
  });
}

// ------------------------------------------------------------
// Payload
// ------------------------------------------------------------

const value = (id) => Number($(id).value);

/**
 * Build the JSON payload for POST /api/analyze.
 * Throws Error(<message in the current language>) when something is invalid.
 */
export function readForm(location) {
  if (location.lat === null || location.lon === null) {
    throw new Error(t("err.no_location"));
  }

  const targetPct = value("targetRenewable");
  if (!targetPct || targetPct < 1 || targetPct > 100) {
    throw new Error(t("err.target"));
  }

  // equipment settings (PV performance factor, battery efficiency)
  const pvFactor = value("pvFactor");
  if (!(pvFactor >= 0.3 && pvFactor <= 1)) throw new Error(t("err.pv_factor"));

  const batteryEff = value("batteryEff");
  if (!(batteryEff >= 0.5 && batteryEff <= 1)) throw new Error(t("err.batt_eff"));

  const payload = {
    lang: getLang(),
    pv_performance_factor: pvFactor,
    battery_efficiency: batteryEff,
    lat: location.lat,
    lon: location.lon,
    input_mode: state.mode,
    year: value("year"),
    target_renewable_fraction: targetPct / 100,
  };

  // optional elevation typed by the user
  const elevationText = $("elevation").value.trim();
  if (elevationText !== "") {
    const elevation = Number(elevationText);
    if (!Number.isFinite(elevation) || elevation < -430 || elevation > 8850) {
      throw new Error(t("err.elevation"));
    }
    payload.elevation_m = elevation;
  } else if (state.autoElevation !== null) {
    // the value the page already found from the map
    payload.elevation_hint_m = state.autoElevation;
  }

  if (state.mode === "monthly") {
    const texts = monthInputs().map((input) => input.value.trim());
    const values = texts.map(Number);

    if (
      texts.some((text) => text === "") ||
      values.some((v) => !Number.isFinite(v) || v < 0) ||
      values.every((v) => v === 0)
    ) {
      throw new Error(t("err.months"));
    }

    payload.monthly_values = values;
  } else {
    if (!state.hourly) {
      throw new Error(state.hourlyError || t("err.file_missing"));
    }
    payload.hourly_kwh = state.hourly;
  }

  return payload;
}

/** Remember the elevation found for the clicked point (null = unknown). */
export function setAutoElevation(value) {
  state.autoElevation = value;
}
