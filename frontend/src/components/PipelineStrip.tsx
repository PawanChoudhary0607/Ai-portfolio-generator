import { useEffect, useState } from "react";

export interface PipelineStage {
  label: string;
  detail: string;
}

const DEFAULT_STAGES: PipelineStage[] = [
  { label: "Uploading resume", detail: "Your PDF is received and queued for processing." },
  { label: "Extracting text", detail: "PyMuPDF pulls structured text from every page of the PDF." },
  { label: "AI analysis", detail: "A local Qwen3 model reads your experience and identifies your strengths." },
  { label: "Generating portfolio", detail: "Hero, about, skills, and project sections are written and structured." },
  { label: "Building website", detail: "Content is rendered into your chosen theme as a static site." },
  { label: "Done", detail: "Your portfolio is ready to preview, switch themes on, and export." },
];

interface PipelineStripProps {
  stages?: PipelineStage[];
  /** Milliseconds each stage is held before advancing. */
  intervalMs?: number;
}

/**
 * The landing page's one signature motion element: a live filmstrip of the
 * actual generation pipeline, cycling continuously. This mirrors the real
 * step order used by the engine (extraction -> analysis -> portfolio ->
 * website), so the numbered sequence here encodes real information rather
 * than decorating the section.
 */
export function PipelineStrip({ stages = DEFAULT_STAGES, intervalMs = 1700 }: PipelineStripProps) {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReducedMotion) {
      setActive(stages.length - 1);
      return;
    }
    const id = window.setInterval(() => {
      setActive((prev) => (prev + 1) % stages.length);
    }, intervalMs);
    return () => window.clearInterval(id);
  }, [stages.length, intervalMs]);

  return (
    <div>
      {/* Filmstrip — horizontally scrollable on narrow screens so stages never get clipped */}
      <div className="-mx-1 overflow-x-auto px-1 pb-1">
      <div className="flex min-w-[640px] items-start">
        {stages.map((stage, i) => {
          const isDone = i < active;
          const isActive = i === active;
          const isLast = i === stages.length - 1;
          return (
            <div key={stage.label} className="flex flex-1 flex-col items-start">
              <div className="flex w-full items-center">
                <span
                  className={[
                    "flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border text-[10px] font-mono transition-colors duration-500",
                    isDone
                      ? "border-ink-900 bg-ink-900 text-white"
                      : isActive
                        ? "border-accent-600 bg-accent-600 text-white"
                        : "border-ink-300 bg-white text-ink-300",
                  ].join(" ")}
                  aria-hidden="true"
                >
                  {isDone ? "✓" : String(i + 1).padStart(2, "0")}
                </span>
                {!isLast && (
                  <span className="relative mx-1 h-px flex-1 overflow-hidden bg-ink-200">
                    <span
                      className="absolute inset-y-0 left-0 bg-ink-900 transition-all duration-500"
                      style={{ width: isDone ? "100%" : "0%" }}
                    />
                  </span>
                )}
              </div>
              <span
                className={[
                  "eyebrow mt-3 pr-2 leading-snug transition-colors duration-500",
                  isActive ? "text-ink-900" : isDone ? "text-ink-500" : "text-ink-300",
                ].join(" ")}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
      </div>

      {/* Detail line for the active stage */}
      <p key={active} className="mt-6 animate-fade-up text-sm leading-relaxed text-ink-500" aria-live="polite">
        {stages[active].detail}
      </p>
    </div>
  );
}
