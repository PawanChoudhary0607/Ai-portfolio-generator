export type ThemePreference = "light" | "dark" | "system";
export type AccentPreference = "orange" | "blue" | "emerald" | "purple" | "rose";

export const THEME_STORAGE_KEY = "portfolio_ai_theme";
export const ACCENT_STORAGE_KEY = "portfolio_ai_accent";

export const accentOptions: { value: AccentPreference; label: string }[] = [
  { value: "orange", label: "Orange" },
  { value: "blue", label: "Blue" },
  { value: "emerald", label: "Emerald" },
  { value: "purple", label: "Purple" },
  { value: "rose", label: "Rose" },
];

export function getStoredTheme(): ThemePreference {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  return stored === "light" || stored === "dark" || stored === "system" ? stored : "system";
}

export function getStoredAccent(): AccentPreference {
  const stored = localStorage.getItem(ACCENT_STORAGE_KEY);
  return accentOptions.some((option) => option.value === stored) ? (stored as AccentPreference) : "orange";
}

function resolveTheme(theme: ThemePreference): "light" | "dark" {
  if (theme !== "system") return theme;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyAppearance(theme: ThemePreference, accent: AccentPreference) {
  const root = document.documentElement;
  root.dataset.theme = resolveTheme(theme);
  root.dataset.themePreference = theme;
  root.dataset.accent = accent;
}

export function persistAppearance(theme: ThemePreference, accent: AccentPreference) {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
  localStorage.setItem(ACCENT_STORAGE_KEY, accent);
  applyAppearance(theme, accent);
}
