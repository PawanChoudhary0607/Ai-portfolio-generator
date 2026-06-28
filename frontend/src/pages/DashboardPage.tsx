import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card, Badge } from "@/components/Card";
import { Button } from "@/components/Button";
import { ThemeSwatch } from "@/components/ThemeSwatch";
import { EmptyState } from "@/components/EmptyState";
import { SkeletonRow } from "@/components/Skeleton";
import { dashboardApi } from "@/api/client";
import { resumeStatusBadge, portfolioStatusBadge } from "@/lib/status";
import { useAuth } from "@/context/AuthContext";
import type { DashboardOverview } from "@shared/types";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/** Resume statuses where there's nothing more to watch happen. */
const TERMINAL_RESUME_STATUSES = new Set(["failed"]);

export function DashboardPage() {
  const { user } = useAuth();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    dashboardApi
      .overview()
      .then(setOverview)
      .catch(() => setError("Couldn't load your dashboard. Please refresh."));
  }, []);

  const firstName = user?.full_name?.split(" ")[0];
  const hasPortfolios = (overview?.generated_portfolios.length ?? 0) > 0;
  const hasResumes = (overview?.recent_resumes.length ?? 0) > 0;
  const isEmpty = overview && !hasPortfolios && !hasResumes;

  return (
    <div className="mx-auto max-w-4xl px-8 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">
            {firstName ? `Welcome back, ${firstName}` : "Dashboard"}
          </h1>
          <p className="mt-1 text-sm text-ink-500">Your resumes and generated portfolios.</p>
        </div>
        <Link to="/upload">
          <Button>Upload a resume</Button>
        </Link>
      </div>

      {error && <p className="mt-6 text-sm text-danger">{error}</p>}

      {!overview && !error && (
        <div className="mt-8 space-y-3">
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
        </div>
      )}

      {isEmpty && (
        <Card className="mt-8">
          <EmptyState
            title="Upload your first resume to get started"
            description="Drop in a PDF and Portfolio AI will extract your experience and generate a portfolio from it — usually in under a minute."
            action={
              <Link to="/upload">
                <Button>Upload a resume</Button>
              </Link>
            }
          />
        </Card>
      )}

      {overview && !isEmpty && (
        <>
          {/* Primary: the actual output the product delivers */}
          <section className="mt-8">
            <h2 className="text-sm font-semibold text-ink-900">Your portfolios</h2>
            {!hasPortfolios ? (
              <Card className="mt-3">
                <EmptyState
                  title="Your portfolio will appear here"
                  description="It shows up automatically once your most recent resume finishes processing."
                />
              </Card>
            ) : (
              <Card className="mt-3 divide-y divide-ink-200">
                {overview.generated_portfolios.map((p) => {
                  const badge = portfolioStatusBadge(p.status);
                  return (
                    <Link
                      key={p.id}
                      to={`/portfolios/${p.id}`}
                      className="flex items-center gap-4 px-5 py-3 transition-colors hover:bg-ink-100/60"
                    >
                      <ThemeSwatch theme={p.selected_theme ?? "minimal"} className="h-10 w-14 flex-shrink-0" />
                      <span className="flex-1 truncate text-sm text-ink-900">{p.title}</span>
                      <Badge tone={badge.tone}>{badge.label}</Badge>
                      <span className="hidden text-xs text-ink-500 sm:inline">{formatDate(p.updated_at)}</span>
                    </Link>
                  );
                })}
              </Card>
            )}
          </section>

          {/* Secondary: upload history, smaller and quieter — mainly useful while something is still processing */}
          {hasResumes && (
            <section className="mt-8">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-ink-500">Recent uploads</h2>
              <ul className="mt-2 divide-y divide-ink-200 border-t border-ink-200">
                {overview.recent_resumes.map((r) => {
                  const badge = resumeStatusBadge(r.status);
                  const canResume = !TERMINAL_RESUME_STATUSES.has(r.status);
                  return (
                    <li key={r.id} className="flex items-center gap-3 py-2.5 text-sm">
                      <span className="flex-1 truncate text-ink-700">{r.original_filename}</span>
                      <Badge tone={badge.tone}>{badge.label}</Badge>
                      <span className="hidden text-xs text-ink-500 sm:inline">{formatDate(r.created_at)}</span>
                      {canResume && (
                        <Link to={`/upload?resume=${r.id}`} className="text-xs font-medium text-accent-600 hover:text-accent-700">
                          View progress
                        </Link>
                      )}
                    </li>
                  );
                })}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  );
}

