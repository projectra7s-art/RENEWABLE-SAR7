// Entry point: wires the map, the form, the API and the results together.

import { analyze, fetchElevation } from "./api.js";
import { initForm, readForm, setAutoElevation } from "./form.js";
import { initI18n, setLang, getLang, t } from "./i18n.js";
import { getLocation, initMap, searchPlace } from "./map.js";
import { initResults, renderResults } from "./results.js";
import { getTheme, initTheme, toggleTheme } from "./theme.js";
import { num } from "./format.js";
import { $, clearError, hide, setBusy, setText, show, showError } from "./ui.js";

// ------------------------------------------------------------
// Elevation of the clicked point
// ------------------------------------------------------------

let elevationRequest = 0;

async function onLocationSelected({ lat, lon }) {
  const request = ++elevationRequest;
  setText("elevText", t("loc.elev.loading"));
  setAutoElevation(null);

  const elevation = await fetchElevation(lat, lon);
  if (request !== elevationRequest) return; // a newer click is pending

  setAutoElevation(elevation);
  setText("elevText", elevation === null ? t("loc.elev.na") : `${num(elevation, 0)} m`);

  // show the automatic value inside the optional override box as well
  $("elevation").placeholder = elevation === null ? "" : `${num(elevation, 0)}  (${t("elev.auto")})`;
}

// ------------------------------------------------------------
// Analysis
// ------------------------------------------------------------

async function runAnalysis() {
  clearError();

  let payload;
  try {
    payload = readForm(getLocation());
  } catch (error) {
    showError(error.message);
    return;
  }

  setBusy(true);
  hide("results");
  show("loading");

  try {
    const data = await analyze(payload);

    // Show the section first so Chart.js measures the real canvas size.
    hide("loading");
    show("results");
    renderResults(data);

    window.scrollTo({
      top: $("results").offsetTop - 90,   // keep the heading below the sticky bar
      behavior: "smooth",
    });
  } catch (error) {
    hide("loading");
    showError(error.message);
  } finally {
    setBusy(false);
  }
}

initTheme();
initI18n();
initMap(onLocationSelected);
initForm();
initResults();

// the theme button's tooltip names the mode it switches to
function updateThemeTitle() {
  $("themeBtn").title = t(getTheme() === "dark" ? "theme.light" : "theme.dark");
}
updateThemeTitle();
document.addEventListener("themechange", updateThemeTitle);
document.addEventListener("languagechange", updateThemeTitle);

$("themeBtn").addEventListener("click", toggleTheme);
$("langBtn").addEventListener("click", () =>
  setLang(getLang() === "ar" ? "en" : "ar")
);
$("runBtn").addEventListener("click", runAnalysis);

// place search: only when the user presses Enter (Nominatim usage policy)
$("placeSearch").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchPlace(event.target.value);
  }
});
