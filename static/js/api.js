// Backend calls.

import { t } from "./i18n.js";

export async function analyze(payload) {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    // the server returned something that is not JSON (e.g. a gateway timeout)
  }

  if (!response.ok) {
    throw new Error(
      (data && data.error) || t("err.server", { status: response.status })
    );
  }

  return data;
}

// Elevation of a clicked point (metres, or null when nobody could answer).
// The server tries three providers; if it cannot reach them, the browser asks
// Open-Meteo directly (it allows browser requests).
export async function fetchElevation(lat, lon) {
  try {
    const response = await fetch(`/api/elevation?lat=${lat}&lon=${lon}`);
    if (response.ok) {
      const data = await response.json();
      if (data.elevation_m !== null && data.elevation_m !== undefined) {
        return data.elevation_m;
      }
    }
  } catch {
    // fall through to the direct request
  }

  try {
    const response = await fetch(
      `https://api.open-meteo.com/v1/elevation?latitude=${lat}&longitude=${lon}`
    );
    const data = await response.json();
    const value = Array.isArray(data.elevation) ? data.elevation[0] : data.elevation;
    return typeof value === "number" ? Math.round(value) : null;
  } catch {
    return null;
  }
}
