// Night / day mode. The choice is remembered; the first visit follows the
// device setting.

const STORAGE_KEY = "resizer.theme";

export function getTheme() {
  return document.documentElement.dataset.theme || "light";
}

function apply(theme) {
  document.documentElement.dataset.theme = theme;
  document.dispatchEvent(new CustomEvent("themechange"));
}

export function initTheme() {
  let saved = null;
  try {
    saved = localStorage.getItem(STORAGE_KEY);
  } catch {
    // storage may be blocked
  }

  const preferred =
    saved ||
    (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light");

  document.documentElement.dataset.theme = preferred === "dark" ? "dark" : "light";
}

export function toggleTheme() {
  const next = getTheme() === "dark" ? "light" : "dark";

  try {
    localStorage.setItem(STORAGE_KEY, next);
  } catch {
    // ignore
  }

  apply(next);
}
