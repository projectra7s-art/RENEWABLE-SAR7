// Results: scenario cards side by side + details of the chosen scenario.
//
// Any element with  data-bind="path.in.view"  (and optionally
// data-fmt="kw|kwh|sar|pct|...") is filled automatically, so adding a new
// number to the page needs HTML only. The "view" is the site-level data plus
// the chosen scenario (recommended, economics, performance, chart).

import { FORMATTERS, num } from "./format.js";
import { renderDailyChart, renderMixChart, renderMonthlyChart } from "./charts.js";
import { t } from "./i18n.js";
import { $, setText } from "./ui.js";

const state = {
  data: null,        // last /api/analyze response
  tab: "overview",   // "overview" or a scenario id
  selectedId: null,  // scenario used by the details and the charts
  period: "all",     // daily-chart period: "all" or 0..11
};

function get(object, path) {
  return path
    .split(".")
    .reduce((o, key) => (o == null ? undefined : o[key]), object);
}

const chosenScenario = () =>
  state.data.scenarios.find((s) => s.id === state.selectedId);

// ------------------------------------------------------------
// Scenario cards (overview tab)
// ------------------------------------------------------------

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function icon(name, className) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", `#${name}`);
  svg.append(use);
  svg.setAttribute("class", className);
  return svg;
}

function row(label, value, className = "scn-row") {
  const node = el("div", className);
  node.append(el("span", "", label), el("b", "", "\u200E" + value));
  return node;
}

// which technologies a scenario uses -> icons in the card header
const SCENARIO_ICONS = {
  solar_battery: ["i-sun i-pv"],
  wind_battery: ["i-wind i-wind"],
  hybrid: ["i-sun i-pv", "i-wind i-wind"],
};

function scenarioCard(scenario) {
  const rec = scenario.recommended;
  const perf = scenario.performance;
  const eco = scenario.economics;

  const card = el("article", "scenario-card");
  card.dataset.id = scenario.id;

  if (scenario.cheapest) {
    card.classList.add("is-best");
    card.append(el("span", "ribbon", t("scn.badge.cheapest")));
  }

  const icons = el("div", "scn-icons");
  (SCENARIO_ICONS[scenario.id] || []).forEach((spec) => {
    const [symbol, cls] = spec.split(" ");
    icons.append(icon(symbol, cls));
  });

  const head = el("div", "scn-head");
  head.append(icons, el("h3", "", t(`tab.${scenario.id}`)));
  card.append(head);

  if (!perf.target_met) {
    // reached the maximum allowed quantity and still missed the target
    const key = scenario.limits_hit.length ? "scn.badge.limit" : "scn.badge.unmet";
    card.append(el("span", "badge-unmet", t(key)));
    card.classList.add("infeasible");
  }

  // total cost, large
  const cost = el("div", "scn-cost");
  const amount = el("b", "", num(eco.capital_cost_sar, 0) + " ");
  amount.append(el("small", "", "SAR"));
  cost.append(el("span", "", t("scn.capex")), amount);
  card.append(cost);

  // renewable share as a bar, with a tick at the target
  const rf = Number(perf.renewable_fraction_pct) || 0;
  const target = Number(state.data.target?.renewable_fraction_pct) || 0;
  const clamp = (v) => Math.max(0, Math.min(100, v));

  const meterHead = el("div", "scn-meter-head");
  meterHead.append(el("span", "", t("scn.rf")), el("b", "", `${num(rf, 1)}%`));

  const meter = el("div", perf.target_met ? "meter" : "meter short");
  const fill = el("div", "meter-fill");
  fill.style.width = `${clamp(rf)}%`;
  const tick = el("div", "meter-target");
  tick.style.insetInlineStart = `${clamp(target)}%`;
  tick.title = `${t("kpi.target")}: ${num(target, 0)}%`;
  meter.append(fill, tick);

  const meterBox = el("div", "scn-meter");
  meterBox.append(meterHead, meter,
    el("div", "meter-caption", `${t("kpi.target")}: ${num(target, 0)}%`));
  card.append(meterBox);

  const count = (n, detail) => `${num(n, 0)}${n > 0 ? ` (${detail})` : ""}`;

  const rows = el("div", "scn-rows");
  rows.append(
    row(t("scn.pv"), count(rec.pv_panels, `${num(rec.pv_panel_w, 0)} W`),
        rec.pv_panels === 0 ? "scn-row zero" : "scn-row"),
    row(t("scn.wind"), count(rec.wind_turbines, `${num(rec.wind_turbine_kw, 1)} kW`),
        rec.wind_turbines === 0 ? "scn-row zero" : "scn-row"),
    row(t("scn.battery"), count(rec.battery_units, `${num(rec.battery_unit_kwh, 0)} kWh`),
        rec.battery_units === 0 ? "scn-row zero" : "scn-row"),
  );
  card.append(rows);

  const button = el("button", "ghost-btn scn-btn", t("scn.choose"));
  button.type = "button";
  button.addEventListener("click", () => setTab(scenario.id));
  card.append(button);

  return card;
}

function renderScenarioCards() {
  $("scenarioGrid").replaceChildren(...state.data.scenarios.map(scenarioCard));
}

// ------------------------------------------------------------
// Details of the chosen scenario
// ------------------------------------------------------------

function bindAll(view) {
  // elements that make no sense without a value (e.g. temperature when it is
  // ignored) are hidden
  document.querySelectorAll("[data-hide-if-null]").forEach((element) => {
    const value = get(view, element.dataset.hideIfNull);
    element.classList.toggle("hidden", value === undefined || value === null);
  });

  document.querySelectorAll("[data-bind]").forEach((element) => {
    const raw = get(view, element.dataset.bind);
    const format = FORMATTERS[element.dataset.fmt || "text"];

    // \u200E (left-to-right mark) keeps "59,550 SAR" in the right order
    // inside an RTL page.
    element.textContent =
      raw === undefined || raw === null ? "--" : "\u200E" + format(raw);
  });
}

function renderTargetStatus(view) {
  const met = view.performance.target_met;
  setText("targetStatus", t(met ? "kpi.met" : "kpi.unmet"));
  $("targetStatus").dataset.met = String(met);
}

// A component with quantity 0 is not used: dim its card and hide the
// details of the (unused) equipment model.
function renderUnusedComponents(view) {
  document.querySelectorAll("[data-count-path]").forEach((card) => {
    const unused = Number(get(view, card.dataset.countPath)) === 0;

    card.classList.toggle("kpi--off", unused);
    card.querySelector(".kpi-details").classList.toggle("hidden", unused);
    card.querySelector(".kpi-off-note").classList.toggle("hidden", !unused);
  });
}

// A scenario that used the maximum allowed quantity and still misses the
// target is explained, so the big numbers (e.g. 50 batteries) are not a surprise.
function renderLimitNotice(view) {
  const box = $("limitNotice");
  const hit = view.limits_hit || [];
  const missed = !view.performance.target_met;

  if (!missed || hit.length === 0) {
    box.classList.add("hidden");
    return;
  }

  const items = hit
    .map((name) => t(`limit.${name}`, { n: num(view.limits[name], 0) }))
    .join(" • ");

  box.textContent = t("notice.limit", {
    items,
    rf: num(view.performance.renewable_fraction_pct, 1),
    target: num(view.target.renewable_fraction_pct, 0),
  });
  box.classList.remove("hidden");
}

function renderSources(view) {
  const weather = view.weather;

  setText("elevationSource", `(${t(`src.${weather.elevation_source}`)})`);

  const shear =
    weather.wind_shear_source === "default" ? "default" : "nasa";
  setText("shearSource", `(${t(`src.shear.${shear}`)})`);

  const method = view.load.method;
  setText(
    "loadMethod",
    t(`method.${method.code}`, { tariff: method.tariff })
  );
}

// One sentence that explains, with numbers, why PV or wind is cheaper.
function renderComparison(view) {
  const { pv, wind } = view.comparison;
  let text = "";

  if (pv.sar_per_kwh && wind.sar_per_kwh) {
    const ratio = wind.sar_per_kwh / pv.sar_per_kwh;

    if (ratio > 1.05) {
      text = t("cmp.wind_worse", { ratio: ratio.toFixed(1) });
    } else if (ratio < 0.95) {
      text = t("cmp.wind_better", { ratio: ratio.toFixed(2) });
    } else {
      text = t("cmp.similar");
    }
    text += t("cmp.note");
  }

  setText("comparisonNote", text);
}

// ------------------------------------------------------------
// Cost breakdown: price of ONE unit, quantity, total, life, yearly installment
// ------------------------------------------------------------

function cell(tag, text, className) {
  const node = el(tag, className || "", text);
  return node;
}

function renderCostBreakdown(scenario) {
  const costs = scenario.costs;

  const table = $("costTable");
  table.replaceChildren();

  const head = el("thead");
  const headRow = el("tr");
  ["item", "unit", "qty", "total"].forEach((key) =>
    headRow.append(cell("th", t(`cost.col.${key}`)))
  );
  head.append(headRow);

  const body = el("tbody");
  costs.rows.forEach((item) => {
    const name = t(`cost.item.${item.category}`) +
      (item.model ? ` (${item.model})` : "");
    const tr = el("tr");
    tr.append(
      cell("td", name),
      cell("td", `\u200E${num(item.unit_price_sar, 0)} SAR`),
      cell("td", `\u200E${num(item.quantity, 0)}`),
      cell("td", `\u200E${num(item.total_sar, 0)} SAR`),
    );
    body.append(tr);
  });

  const foot = el("tfoot");
  const footRow = el("tr");
  footRow.append(
    cell("td", t("cost.row.total")),
    cell("td", ""),
    cell("td", ""),
    cell("td", `\u200E${num(costs.capital_total_sar, 0)} SAR`),
  );
  foot.append(footRow);
  table.append(head, body, foot);
}

function renderPeriodOptions() {
  const select = $("periodSelect");
  select.replaceChildren();

  const add = (value, label) => {
    const option = el("option", "", label);
    option.value = value;
    select.append(option);
  };

  add("all", t("chart.whole_year"));
  for (let m = 1; m <= 12; m++) add(String(m - 1), t(`month.${m}`));

  select.value = String(state.period);
}

function periodLabel() {
  return state.period === "all"
    ? t("chart.whole_year")
    : t(`month.${Number(state.period) + 1}`);
}

function renderDetails() {
  const scenario = chosenScenario();
  const view = { ...state.data, ...scenario };

  bindAll(view);
  renderUnusedComponents(view);
  renderTargetStatus(view);
  renderLimitNotice(view);
  renderSources(view);
  renderComparison(view);
  renderCostBreakdown(scenario);

  setText("detailsTitle", t("scn.details", { label: t(`scn.${scenario.id}`) }));
  setText(
    "monthlyTitle",
    `${t("chart.monthly.title")} (${t(`tab.${scenario.id}`)})`
  );
  setText("chartDesc", t("chart.day.desc", { period: periodLabel() }));

  renderMonthlyChart(scenario.monthly);
  renderMixChart(scenario.energy_mix);
  renderDailyChart(scenario.chart, state.period);
}

// ------------------------------------------------------------
// Public API
// ------------------------------------------------------------

// "overview" shows the three cards and the charts of the recommended
// scenario; a scenario tab shows that scenario's details and charts.
function setTab(tab) {
  state.tab = tab;
  state.selectedId = tab === "overview" ? state.data.recommended_id : tab;

  $("results").dataset.tab = tab;
  document.querySelectorAll(".rtab").forEach((button) =>
    button.classList.toggle("active", button.dataset.tab === tab)
  );

  renderDetails();
}

export function renderResults(data) {
  state.data = data;
  state.period = "all";

  renderPeriodOptions();
  renderScenarioCards();
  setTab("overview");
}

export function initResults() {
  document.querySelectorAll(".rtab").forEach((button) =>
    button.addEventListener("click", () => setTab(button.dataset.tab))
  );

  $("periodSelect").addEventListener("change", (event) => {
    state.period = event.target.value;
    setText("chartDesc", t("chart.day.desc", { period: periodLabel() }));
    renderDailyChart(chosenScenario().chart, state.period);
  });

  // charts pick their colors from the theme
  document.addEventListener("themechange", () => {
    if (state.data) renderDetails();
  });

  // switching language re-renders every text that JavaScript produced
  document.addEventListener("languagechange", () => {
    if (!state.data) return;
    renderPeriodOptions();
    renderScenarioCards();
    renderDetails();
  });
}
