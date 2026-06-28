import { useEffect, useState } from "react";
import { Card } from "@/components/Card";
import { portfolioApi } from "@/api/client";
import type { Theme } from "@shared/types";

const STORAGE_KEY = "portfolio_ai_settings";

interface LocalSettings {
  defaultTheme: string;
}

function loadSettings(): LocalSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { defaultTheme: "", ...JSON.parse(raw) };
  } catch {
    // Fall back to defaults.
  }
  return { defaultTheme: "" };
}

function SettingsRow({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 border-b border-ink-200 px-5 py-5 last:border-b-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="max-w-sm">
        <p className="text-sm font-medium text-ink-900">{title}</p>
        <p className="mt-0.5 text-sm text-ink-500">{description}</p>
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  );
}

export function SettingsPage() {
  const [settings, setSettings] = useState<LocalSettings>(loadSettings);
  const [saved, setSaved] = useState(false);
  const [themes, setThemes] = useState<Theme[]>([]);

  useEffect(() => {
    portfolioApi
      .themeCatalog()
      .then((catalog) => {
        setThemes(catalog);
        if (!settings.defaultTheme && catalog.length > 0) {
          update({ defaultTheme: catalog[0].value });
        }
      })
      .catch(() => {
        // Settings still works without the catalog; the select stays empty.
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function update(partial: Partial<LocalSettings>) {
    setSettings((prev) => {
      const next = { ...prev, ...partial };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      setSaved(true);
      window.setTimeout(() => setSaved(false), 1500);
      return next;
    });
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-8 sm:px-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">Settings</h1>
          <p className="mt-1 text-sm text-ink-500">Preferences for how new portfolios are created.</p>
        </div>
        {saved && <span className="text-xs font-medium text-success">Saved</span>}
      </div>

      <Card className="mt-6">
        <SettingsRow
          title="Default theme"
          description="Used to pre-select a theme the next time you generate a portfolio."
        >
          <select
            value={settings.defaultTheme}
            onChange={(e) => update({ defaultTheme: e.target.value })}
            className="h-9 rounded-md border border-ink-200 bg-white px-3 text-sm text-ink-900 outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500"
          >
            {themes.length === 0 && <option value="">Loading...</option>}
            {themes.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </SettingsRow>

        <SettingsRow
          title="AI engine"
          description="Resumes are analyzed by a local AI engine configured by your administrator."
        >
          <span className="rounded-full bg-ink-100 px-3 py-1 text-xs font-medium text-ink-500">
            Managed locally
          </span>
        </SettingsRow>
      </Card>
    </div>
  );
}
