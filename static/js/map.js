// Leaflet map: search a place or click anywhere in the world.

import { t } from "./i18n.js";
import { setText } from "./ui.js";

const selected = { lat: null, lon: null };
let map = null;
let marker = null;
let onSelectCallback = null;

function select(lat, lon) {
  // keep latitude valid, wrap longitude into [-180, 180)
  lat = Math.max(-90, Math.min(90, Number(lat)));
  lon = ((Number(lon) + 180) % 360 + 360) % 360 - 180;

  selected.lat = lat;
  selected.lon = lon;

  setText("latText", lat.toFixed(6));
  setText("lonText", lon.toFixed(6));

  if (marker) map.removeLayer(marker);
  marker = L.marker([lat, lon]).addTo(map);

  if (onSelectCallback) onSelectCallback({ lat, lon });
}

export function initMap(onSelect) {
  onSelectCallback = onSelect;
  map = L.map("map").setView([20, 0], 2);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  map.on("click", (event) => select(event.latlng.lat, event.latlng.lng));
}

/**
 * Find a place by name (OpenStreetMap Nominatim) and select it.
 * Called only when the user presses Enter, as the service asks.
 */
export async function searchPlace(query) {
  const status = document.getElementById("searchStatus");
  status.classList.remove("bad");
  status.textContent = "";

  query = query.trim();
  if (!query) return;

  try {
    const url =
      "https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=" +
      encodeURIComponent(query);
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    const results = await response.json();

    if (!Array.isArray(results) || results.length === 0) {
      throw new Error("not found");
    }

    const lat = Number(results[0].lat);
    const lon = Number(results[0].lon);

    map.setView([lat, lon], 9);
    select(lat, lon);
    status.textContent = results[0].display_name || "";
  } catch {
    status.textContent = t("loc.search.none");
    status.classList.add("bad");
  }
}

export function getLocation() {
  return { ...selected };
}
