export type Theme = "light" | "dark";
export const THEME_KEY = "canopy-theme";

export function storedTheme(): Theme | null {
  try {
    const v = localStorage.getItem(THEME_KEY);
    return v === "light" || v === "dark" ? v : null;
  } catch {
    return null;
  }
}

export function systemTheme(): Theme {
  return typeof matchMedia === "function" && matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function resolveTheme(): Theme {
  return storedTheme() ?? systemTheme();
}

export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute("data-theme", theme);
}

export function setTheme(theme: Theme): void {
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* storage unavailable — still apply for this session */
  }
  applyTheme(theme);
}

export function toggleTheme(): Theme {
  const next: Theme = resolveTheme() === "dark" ? "light" : "dark";
  setTheme(next);
  return next;
}
