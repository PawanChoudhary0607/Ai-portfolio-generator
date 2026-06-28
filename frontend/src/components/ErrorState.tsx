import { Button } from "@/components/Button";

interface ErrorStateProps {
  /** Plain-language description of what went wrong. Never pass raw API/stack-trace text here. */
  problem: string;
  reason?: string;
  fix?: string;
  onRetry?: () => void;
  retryLabel?: string;
}

/**
 * The single error pattern used everywhere in the app. Backend error
 * messages are already sanitized server-side (see generator_service.py),
 * but this component's job is presentation, not trust — it only ever
 * renders the plain-language copy it's given.
 */
export function ErrorState({ problem, reason, fix, onRetry, retryLabel = "Try again" }: ErrorStateProps) {
  return (
    <div className="rounded-lg border border-danger/20 bg-red-50/60 p-5">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-danger/10 font-mono text-xs text-danger">
          !
        </span>
        <div className="flex-1 space-y-2">
          <p className="text-sm font-medium text-ink-900">{problem}</p>
          {reason && (
            <p className="text-sm text-ink-700">
              <span className="font-medium text-ink-500">Possible reason: </span>
              {reason}
            </p>
          )}
          {fix && (
            <p className="text-sm text-ink-700">
              <span className="font-medium text-ink-500">Suggested fix: </span>
              {fix}
            </p>
          )}
          {onRetry && (
            <div className="pt-1">
              <Button variant="secondary" size="sm" onClick={onRetry}>
                {retryLabel}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
