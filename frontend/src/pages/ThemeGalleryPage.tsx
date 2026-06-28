import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/Button";
import { SkeletonCard } from "@/components/Skeleton";
import { ThemePreview } from "@/components/ThemePreview";
import { ErrorState } from "@/components/ErrorState";
import { portfolioApi } from "@/api/client";
import type { Theme } from "@shared/types";

export function ThemeGalleryPage() {
  const [themes, setThemes] = useState<Theme[] | null>(null);
  const [error, setError] = useState(false);
  const [previewTheme, setPreviewTheme] = useState<Theme | null>(null);
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewError, setPreviewError] = useState<string | null>(null);

  useEffect(() => {
    portfolioApi
      .themeCatalog()
      .then(setThemes)
      .catch(() => setError(true));
  }, []);

  function handlePreview(theme: Theme) {
    setPreviewTheme(theme);
    setPreviewHtml("");
    setPreviewError(null);
    portfolioApi
      .demoWebsite(theme.value)
      .then(setPreviewHtml)
      .catch((err) => setPreviewError(err instanceof Error ? err.message : "Preview failed."));
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-8 sm:px-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">Theme gallery</h1>
          <p className="mt-1 text-sm text-ink-500">Five production-ready layouts for generated portfolios.</p>
        </div>
        <Link to="/upload">
          <Button>Generate a portfolio</Button>
        </Link>
      </div>

      {error && (
        <div className="mt-6">
          <ErrorState
            problem="We couldn't load the theme catalog."
            reason="The request to the server may have failed or timed out."
            fix="Check your connection and try refreshing the page."
            onRetry={() => window.location.reload()}
          />
        </div>
      )}

      <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {!themes && !error && Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} />)}

        {themes?.map((theme) => (
          <div key={theme.value} className="rounded-xl border border-ink-200 bg-white p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-lift">
            <ThemePreview theme={theme.value} label={theme.label} className="h-44" />
            <div className="mt-4">
              <p className="text-sm font-semibold text-ink-900">{theme.label}</p>
              <p className="mt-1 text-sm leading-relaxed text-ink-500">{theme.description}</p>
            </div>
            <div className="mt-4 flex gap-2">
              <Button variant="secondary" size="sm" onClick={() => handlePreview(theme)}>
                Preview
              </Button>
              <a
                href={`/theme-previews/${theme.value}.png`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex h-8 items-center rounded-md px-3 text-sm font-medium text-accent-600 hover:text-accent-700"
              >
                View full example
              </a>
            </div>
          </div>
        ))}
      </div>

      {previewTheme && (
        <div className="fixed inset-0 z-50 bg-ink-900/50 p-3 sm:p-6" role="dialog" aria-modal="true">
          <div className="mx-auto flex h-full max-w-6xl flex-col overflow-hidden rounded-xl bg-white shadow-lift">
            <div className="flex items-center justify-between border-b border-ink-200 px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-ink-900">{previewTheme.label}</p>
                <p className="text-xs text-ink-500">Bundled demo portfolio</p>
              </div>
              <button
                onClick={() => setPreviewTheme(null)}
                className="flex h-9 w-9 items-center justify-center rounded-md text-ink-500 hover:bg-ink-100 hover:text-ink-900"
                aria-label="Close preview"
              >
                x
              </button>
            </div>
            {previewError ? (
              <div className="p-6">
                <ErrorState
                  problem="We couldn't open this preview."
                  reason={previewError}
                  fix="Try another theme or refresh the page."
                />
              </div>
            ) : previewHtml ? (
              <iframe
                title={`${previewTheme.label} demo website`}
                srcDoc={previewHtml}
                className="min-h-0 flex-1 bg-white"
                sandbox="allow-scripts allow-same-origin allow-popups"
              />
            ) : (
              <div className="flex flex-1 items-center justify-center">
                <span className="h-5 w-5 animate-spin rounded-full border-2 border-ink-300 border-t-ink-900" />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
