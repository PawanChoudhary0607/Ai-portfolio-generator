export type LiveStageState = "pending" | "active" | "done" | "failed";

export interface LiveStage {
  label: string;
  state: LiveStageState;
  /** Shown under the strip only for the currently active or failed stage. */
  detail?: string | null;
}

/**
 * The real, data-driven counterpart to the landing page's PipelineStrip.
 * Same visual language (numbered circles, filling connector lines, mono
 * labels) but driven by actual upload progress and the real
 * ResumeProcessingStep statuses from the backend — nothing here is timed
 * or simulated. A failed stage halts the strip in place rather than
 * continuing to animate.
 */
export function LiveProcessingStrip({ stages }: { stages: LiveStage[] }) {
  const activeOrFailed = stages.find((s) => s.state === "active" || s.state === "failed");

  return (
    <div>
      <div className="-mx-1 overflow-x-auto px-1 pb-1">
      <div className="flex min-w-[640px] items-start">
        {stages.map((stage, i) => {
          const isLast = i === stages.length - 1;
          const next = stages[i + 1];
          return (
            <div key={stage.label} className="flex flex-1 flex-col items-start">
              <div className="flex w-full items-center">
                <span
                  className={[
                    "flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border text-[10px] font-mono transition-colors duration-500",
                    stage.state === "done"
                      ? "border-ink-900 bg-ink-900 text-white"
                      : stage.state === "active"
                        ? "border-accent-600 bg-accent-600 text-white"
                        : stage.state === "failed"
                          ? "border-danger bg-danger text-white"
                          : "border-ink-300 bg-white text-ink-300",
                  ].join(" ")}
                  aria-hidden="true"
                >
                  {stage.state === "done" ? "✓" : stage.state === "failed" ? "✕" : String(i + 1).padStart(2, "0")}
                </span>
                {!isLast && (
                  <span className="relative mx-1 h-px flex-1 overflow-hidden bg-ink-200">
                    <span
                      className={[
                        "absolute inset-y-0 left-0 transition-all duration-500",
                        stage.state === "failed" ? "bg-danger" : "bg-ink-900",
                      ].join(" ")}
                      style={{ width: stage.state === "done" && next ? "100%" : "0%" }}
                    />
                  </span>
                )}
              </div>
              <span
                className={[
                  "eyebrow mt-3 pr-2 leading-snug transition-colors duration-500",
                  stage.state === "active"
                    ? "text-ink-900"
                    : stage.state === "failed"
                      ? "text-danger"
                      : stage.state === "done"
                        ? "text-ink-500"
                        : "text-ink-300",
                ].join(" ")}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
      </div>

      {activeOrFailed?.detail && (
        <p
          className={`mt-6 text-sm leading-relaxed ${
            activeOrFailed.state === "failed" ? "text-danger" : "text-ink-500"
          }`}
          aria-live="polite"
        >
          {activeOrFailed.detail}
        </p>
      )}
    </div>
  );
}
