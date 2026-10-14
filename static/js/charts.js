// Chart.js charts. All values come from the Python result (no fixed data).

import { getLang, t } from "./i18n.js";

const charts = {};

const isDark = () => document.documentElement.dataset.theme === "dark";

// Solar and wind colors are read from the CSS (--pv and --wind in
// static/style.css), so the cards, icons and charts always match.
// To change a color, edit it there only.
const cssVar = (name) =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim();

const COLORS = {
  get solar() { return cssVar("--pv") || "#f2a900"; },
  get wind() { return cssVar("--wind") || "#1e3a8a"; },
  get grid() { return cssVar("--grid") || "#9aa5b4"; },
  get load() { return cssVar("--ink") || "#13233a"; },
  get renewable() { return cssVar("--accent") || "#0f8c6e"; },
  get gridLine() { return isDark() ? "#f27b89" : "#c8384b"; },
};

function applyThemeDefaults() {
  Chart.defaults.color = cssVar("--muted") || "#5b6b7e";
  Chart.defaults.borderColor = isDark()
    ? "rgba(255, 255, 255, 0.08)"
    : "rgba(19, 35, 58, 0.07)";
  Chart.defaults.font.family = '"IBM Plex Sans Arabic", "Segoe UI", sans-serif';
  Chart.defaults.font.size = 12;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
  Chart.defaults.plugins.legend.labels.boxHeight = 8;
  Chart.defaults.plugins.legend.labels.padding = 16;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;
}

function draw(name, canvasId, config) {
  applyThemeDefaults();
  if (charts[name]) charts[name].destroy();
  charts[name] = new Chart(document.getElementById(canvasId), config);
}

// "January" -> "Jan" in English; Arabic month names are already short
function monthLabels() {
  return Array.from({ length: 12 }, (_, i) => {
    const name = t(`month.${i + 1}`);
    return getLang() === "en" ? name.slice(0, 3) : name;
  });
}

/** Monthly production (stacked solar + wind) versus the load line. */
export function renderMonthlyChart(monthly) {
  draw("monthly", "monthlyChart", {
    type: "bar",
    data: {
      labels: monthLabels(),
      datasets: [
        {
          type: "bar",
          label: t("chart.monthly.solar"),
          data: monthly.solar_kwh,
          backgroundColor: COLORS.solar,
          stack: "production",
          borderRadius: 3,
          maxBarThickness: 34,
        },
        {
          type: "bar",
          label: t("chart.monthly.wind"),
          data: monthly.wind_kwh,
          backgroundColor: COLORS.wind,
          stack: "production",
          borderRadius: 3,
          maxBarThickness: 34,
        },
        {
          type: "line",
          label: t("chart.monthly.load"),
          data: monthly.load_kwh,
          borderColor: COLORS.load,
          backgroundColor: COLORS.load,
          borderWidth: 2,
          borderDash: [5, 4],
          tension: 0.3,
          pointRadius: 2.5,
          pointStyle: "line",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "bottom" } },
      scales: {
        x: { stacked: true, grid: { display: false } },
        y: {
          stacked: true,
          border: { display: false },
          beginAtZero: true,
          title: { display: true, text: "kWh" },
        },
      },
    },
  });
}

/** Pie: share of the yearly demand served by solar, wind and the grid. */
export function renderMixChart(mix) {
  draw("mix", "mixChart", {
    type: "doughnut",
    data: {
      labels: [
        t("chart.mix.solar"),
        t("chart.mix.wind"),
        t("chart.mix.grid"),
      ],
      datasets: [{
        data: [mix.solar_pct, mix.wind_pct, mix.grid_pct],
        backgroundColor: [COLORS.solar, COLORS.wind, COLORS.grid],
        borderWidth: 2,
        borderColor: cssVar("--panel") || "#fff",
        hoverOffset: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "72%",
      plugins: {
        legend: { position: "bottom" },
        tooltip: {
          callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.parsed}%` },
        },
      },
    },
  });
}

/**
 * Average day: the mean of every hour of the day.
 * period = "all" (whole year) or 0..11 (one month).
 */
export function renderDailyChart(chart, period) {
  const source = period === "all" ? chart : chart.months[Number(period)];

  const line = (label, data, color, fill = false) => ({
    label,
    data,
    borderColor: color,
    backgroundColor: color + "22",
    fill,
    tension: 0.25,
    borderWidth: 2,
    pointRadius: 0,
    pointHoverRadius: 4,
  });

  draw("daily", "energyChart", {
    type: "line",
    data: {
      labels: chart.hours.map((h) => `${h}:00`),
      datasets: [
        line(t("chart.load"), source.load, COLORS.load),
        line(t("chart.renewable"), source.renewable, COLORS.renewable, true),
        line(t("chart.grid"), source.grid, COLORS.gridLine),
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "bottom" } },
      scales: {
        x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkipPadding: 12 } },
        y: {
          beginAtZero: true,
          border: { display: false },
          title: { display: true, text: "kW" },
        },
      },
    },
  });
}
