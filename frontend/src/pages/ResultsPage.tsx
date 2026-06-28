import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ErrorState } from "@/components/ErrorState";
import { Skeleton } from "@/components/Skeleton";
import { portfolioApi } from "@/api/client";
import type { PortfolioDetail, Theme } from "@shared/types";

interface PortfolioContent {
  hero?: { name?: string; role?: string; headline?: string };
  about?: string;
  skills?: { category?: string; items?: string[] }[];
  projects?: { title?: string; outcome?: string; technologies?: string[] }[];
}

const POLL_INTERVAL_MS = 3000;

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function openHtml(html: string) {
  const url = URL.createObjectURL(new Blob([html], { type: "text/html" }));
  window.open(url, "_blank", "noopener,noreferrer");
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

function fileStem(title: string, theme: string) {
  const safeTitle = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
  return `${safeTitle || "portfolio"}-${theme}`;
}

export function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [portfolio, setPortfolio] = useState<PortfolioDetail | null>(null);
  const [themes, setThemes] = useState<Theme[]>([]);
  const [selectedTheme, setSelectedTheme] = useState("");
  const [previewHtml, setPreviewHtml] = useState("");
  const [loadError, setLoadError] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<"open" | "html" | "zip" | "theme" | null>(null);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    Promise.all([portfolioApi.get(id), portfolioApi.themeCatalog()])
      .then(([p, t]) => {
        if (cancelled) return;
        setPortfolio(p);
        setThemes(t);
        setSelectedTheme(p.selected_theme ?? t[0]?.value ?? "");
        if (p.status === "generating") {
          pollRef.current = window.setInterval(async () => {
            try {
              const latest = await portfolioApi.get(id);
              if (cancelled) return;
              setPortfolio(latest);
              if (latest.status !== "generating" && pollRef.current) {
                window.clearInterval(pollRef.current);
              }
            } catch {
              // Polling can retry on the next tick.
            }
          }, POLL_INTERVAL_MS);
        }
      })
      .catch(() => !cancelled && setLoadError(true));

    return () => {
      cancelled = true;
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [id]);

  useEffect(() => {
    if (!id || !selectedTheme || portfolio?.status !== "draft") return;
    let cancelled = false;
    setBusyAction("theme");
    setActionError(null);
    portfolioApi
      .previewTheme(id, selectedTheme)
      .then((preview) => {
        if (!cancelled) {
          setPreviewHtml(preview.html);
          setPortfolio((prev) => (prev ? { ...prev, selected_theme: selectedTheme } : prev));
        }
      })
      .catch((err) => !cancelled && setActionError(err instanceof Error ? err.message : "Preview failed."))
      .finally(() => !cancelled && setBusyAction(null));
    return () => {
      cancelled = true;
    };
  }, [id, selectedTheme, portfolio?.status]);

  async function handleOpenWebsite() {
    if (!id) return;
    setBusyAction("open");
    setActionError(null);
    try {
      openHtml(await portfolioApi.websiteHtml(id, selectedTheme));
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "We couldn't open your website.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleDownloadHtml() {
    if (!id || !portfolio) return;
    setBusyAction("html");
    setActionError(null);
    try {
      const blob = await portfolioApi.exportHtml(id, selectedTheme);
      saveBlob(blob, `${fileStem(portfolio.title, selectedTheme)}.html`);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "We couldn't download your HTML.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleDownloadZip() {
    if (!id || !portfolio) return;
    setBusyAction("zip");
    setActionError(null);
    try {
      const blob = await portfolioApi.exportZip(id, selectedTheme);
      saveBlob(blob, `${fileStem(portfolio.title, selectedTheme)}.zip`);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "We couldn't download your ZIP.");
    } finally {
      setBusyAction(null);
    }
  }

  if (loadError) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-8 sm:px-8">
        <ErrorState
          problem="We couldn't load this portfolio."
          reason="It may have been removed, or the link may be incorrect."
          fix="Head back to your dashboard and select it from your recent portfolios."
          onRetry={() => window.location.reload()}
        />
        <Link to="/dashboard" className="mt-4 inline-block text-sm font-medium text-accent-600">
          Back to dashboard
        </Link>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-8 sm:px-8">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="mt-3 h-4 w-72" />
        <Skeleton className="mt-6 h-[520px]" />
      </div>
    );
  }

  const content = (portfolio.portfolio_schema_json ?? {}) as PortfolioContent;
  const hero = content.hero ?? {};
  const activeTheme = themes.find((t) => t.value === selectedTheme);
  const isReady = portfolio.status === "draft" && Boolean(portfolio.portfolio_schema_json);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 lg:py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow text-ink-500">Generated website</p>
          <h1 className="mt-2 text-2xl font-semibold text-ink-900">{portfolio.title}</h1>
          <p className="mt-1 text-sm text-ink-500">
            {activeTheme?.label ?? "Theme"} theme - generated {new Date(portfolio.created_at).toLocaleDateString()}
          </p>
        </div>
        <Link to="/upload">
          <Button variant="secondary">Generate another portfolio</Button>
        </Link>
      </div>

      {portfolio.status === "generating" && (
        <div className="mt-6 flex items-center gap-3 rounded-lg border border-ink-200 bg-surface px-4 py-3">
          <span className="h-3.5 w-3.5 flex-shrink-0 animate-spin rounded-full border-2 border-ink-300 border-t-ink-900" />
          <p className="text-sm text-ink-700">Your website is being prepared. This page updates automatically.</p>
        </div>
      )}

      {portfolio.status === "failed" && (
        <div className="mt-6">
          <ErrorState
            problem="Generation didn't finish successfully for this portfolio."
            reason={portfolio.failure_reason ?? undefined}
            fix="Try uploading the resume again from the New portfolio page."
          />
        </div>
      )}

      {isReady && (
        <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
          <section className="overflow-hidden rounded-xl border border-ink-200 bg-white shadow-lift">
            <div className="flex items-center justify-between gap-3 border-b border-ink-200 bg-surface px-4 py-3">
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-danger/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-accent-500/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-success/70" />
              </div>
              <span className="truncate text-xs font-medium text-ink-500">{hero.name ?? portfolio.title}</span>
            </div>
            <iframe
              title="Generated portfolio website preview"
              srcDoc={previewHtml}
              className="h-[620px] w-full bg-white"
              sandbox="allow-scripts allow-same-origin allow-popups"
            />
          </section>

          <aside className="space-y-4">
            <Card className="p-4">
              <p className="text-sm font-semibold text-ink-900">Theme</p>
              <div className="mt-3 grid gap-2">
                {themes.map((theme) => (
                  <button
                    key={theme.value}
                    onClick={() => setSelectedTheme(theme.value)}
                    className={`rounded-lg border px-3 py-2 text-left transition-all ${
                      selectedTheme === theme.value
                        ? "border-accent-500 bg-accent-50 text-accent-700"
                        : "border-ink-200 text-ink-700 hover:border-ink-300 hover:bg-ink-100"
                    }`}
                  >
                    <span className="block text-sm font-medium">{theme.label}</span>
                    <span className="mt-0.5 block text-xs leading-relaxed text-ink-500">{theme.description}</span>
                  </button>
                ))}
              </div>
              {busyAction === "theme" && <p className="mt-3 text-xs text-ink-500">Rendering theme...</p>}
            </Card>

            <Card className="p-4">
              <p className="text-sm font-semibold text-ink-900">Export</p>
              <div className="mt-3 grid gap-2">
                <Button onClick={handleOpenWebsite} isLoading={busyAction === "open"}>
                  Open Website
                </Button>
                <Button variant="secondary" onClick={handleDownloadHtml} isLoading={busyAction === "html"}>
                  Download HTML
                </Button>
                <Button variant="secondary" onClick={handleDownloadZip} isLoading={busyAction === "zip"}>
                  Download ZIP
                </Button>
              </div>
              {actionError && <p className="mt-3 text-sm text-danger">{actionError}</p>}
            </Card>

            <Card className="p-4">
              <p className="text-sm font-semibold text-ink-900">Metadata</p>
              <dl className="mt-3 space-y-2 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-ink-500">Status</dt>
                  <dd className="font-medium capitalize text-ink-900">{portfolio.status}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-ink-500">Theme</dt>
                  <dd className="text-right font-medium text-ink-900">{activeTheme?.label ?? selectedTheme}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-ink-500">Updated</dt>
                  <dd className="font-medium text-ink-900">{new Date(portfolio.updated_at).toLocaleDateString()}</dd>
                </div>
              </dl>
            </Card>
          </aside>
        </div>
      )}

      <details className="mt-6 rounded-xl border border-ink-200 bg-white p-4">
        <summary className="cursor-pointer text-sm font-semibold text-ink-900">View generated content</summary>
        <div className="mt-4 space-y-5">
          <div>
            <p className="text-sm font-medium text-ink-900">{hero.name || "Untitled"}</p>
            {hero.role && <p className="text-sm text-accent-600">{hero.role}</p>}
            {hero.headline && <p className="mt-1 text-sm leading-relaxed text-ink-700">{hero.headline}</p>}
          </div>
          {content.about && (
            <div>
              <p className="text-sm font-medium text-ink-900">About</p>
              <p className="mt-1 text-sm leading-relaxed text-ink-700">{content.about}</p>
            </div>
          )}
          {content.skills && content.skills.length > 0 && (
            <div>
              <p className="text-sm font-medium text-ink-900">Skills</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {content.skills.flatMap((group) =>
                  (group.items ?? []).map((item) => (
                    <span key={`${group.category}-${item}`} className="rounded-full bg-ink-100 px-2.5 py-1 text-xs text-ink-700">
                      {item}
                    </span>
                  )),
                )}
              </div>
            </div>
          )}
          {content.projects && content.projects.length > 0 && (
            <div>
              <p className="text-sm font-medium text-ink-900">Projects</p>
              <div className="mt-2 grid gap-3 sm:grid-cols-2">
                {content.projects.map((project) => (
                  <div key={project.title} className="rounded-lg border border-ink-200 p-3">
                    <p className="text-sm font-medium text-ink-900">{project.title}</p>
                    {project.outcome && <p className="mt-1 text-sm text-ink-500">{project.outcome}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </details>
    </div>
  );
}
