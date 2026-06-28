interface ThemeSwatchProps {
  theme: string;
  className?: string;
}

/**
 * Renders a small abstract mock of each theme's layout rhythm using only
 * color blocks — never a fabricated "generated portfolio" screenshot,
 * since no such portfolio is real until a user creates one.
 */
const PALETTES: Record<string, { bg: string; surface: string; accent: string; text: string }> = {
  minimal: { bg: "#FFFFFF", surface: "#FFF3EC", accent: "#EA580C", text: "#18181B" },
  executive: { bg: "#0B0B0C", surface: "#1C1B19", accent: "#D4AF37", text: "#F4F4F5" },
  developer: { bg: "#111114", surface: "#1A1B1E", accent: "#4ADE80", text: "#E4E4E7" },
  creative: { bg: "#FDF1E8", surface: "#FFD9B8", accent: "#E11D48", text: "#1F1300" },
  saas: { bg: "#F7F8FA", surface: "#E9ECF5", accent: "#4338CA", text: "#111827" },
};

function paletteFor(theme: string) {
  const key = Object.keys(PALETTES).find((k) => theme.toLowerCase().includes(k));
  return PALETTES[key ?? "minimal"];
}

export function ThemeSwatch({ theme, className = "" }: ThemeSwatchProps) {
  const p = paletteFor(theme);
  return (
    <div
      className={`overflow-hidden rounded-lg border border-ink-200 ${className}`}
      style={{ backgroundColor: p.bg }}
      aria-hidden="true"
    >
      <div className="flex h-full flex-col gap-2 p-3">
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: p.accent }} />
          <div className="h-1.5 w-10 rounded-full opacity-40" style={{ backgroundColor: p.text }} />
        </div>
        <div className="h-3 w-2/3 rounded" style={{ backgroundColor: p.text, opacity: 0.85 }} />
        <div className="h-2 w-5/6 rounded" style={{ backgroundColor: p.text, opacity: 0.35 }} />
        <div className="mt-1 grid flex-1 grid-cols-3 gap-1.5">
          <div className="rounded" style={{ backgroundColor: p.surface }} />
          <div className="rounded" style={{ backgroundColor: p.surface }} />
          <div className="rounded" style={{ backgroundColor: p.accent, opacity: 0.85 }} />
        </div>
      </div>
    </div>
  );
}
