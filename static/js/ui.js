// Tiny DOM helpers shared by all modules.

import { t } from "./i18n.js";

export const $ = (id) => document.getElementById(id);

export const show = (id) => $(id).classList.remove("hidden");
export const hide = (id) => $(id).classList.add("hidden");

export function setText(id, value) {
  const element = $(id);
  if (element) element.textContent = value;
}

export function showError(message) {
  setText("error", message);
  show("error");
}

export function clearError() {
  hide("error");
}

export function setBusy(isBusy) {
  const button = $("runBtn");
  button.disabled = isBusy;
  button.querySelector("span").textContent = t(isBusy ? "running" : "run");
}
