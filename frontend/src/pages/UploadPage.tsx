import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { UploadDropzone } from "@/components/UploadDropzone";
import { ProgressBar } from "@/components/ProgressBar";
import { LiveProcessingStrip, type LiveStage } from "@/components/LiveProcessingStrip";
import { ErrorState } from "@/components/ErrorState";
import { resumeApi, ApiError } from "@/api/client";
import type { Resume, ResumeProcessingStatus } from "@shared/types";

type Stage = "idle" | "uploading" | "processing" | "complete" | "failed" | "resuming";

const POLL_INTERVAL_MS = 2000;

/** Maps real upload progress + real backend step statuses onto the six
 * conceptual stages shown to the user. Nothing here is timed or faked —
 * "Uploading" reflects real XHR progress, the middle four are the real
 * ResumeProcessingStep statuses (label/detail included verbatim from the
 * backend), and "Done" reflects the real overall_status. */
function buildStages(stage: Stage, uploadPercent: number, status: ResumeProcessingStatus | null): LiveStage[] {
  const uploadStage: LiveStage =
    stage === "uploading"
      ? { label: "Uploading resume", state: "active", detail: `${uploadPercent}% uploaded` }
      : { label: "Uploading resume", state: "done" };

  if (!status) {
    return [
      uploadStage,
      { label: "Extracting text", state: "pending" },
      { label: "AI analysis", state: "pending" },
      { label: "Generating portfolio", state: "pending" },
      { label: "Building website", state: "pending" },
      { label: "Done", state: "pending" },
    ];
  }

  const stepStages: LiveStage[] = status.steps.map((s) => ({
    label: s.label,
    detail: s.detail,
    state: s.status === "in_progress" ? "active" : s.status === "complete" ? "done" : s.status === "failed" ? "failed" : "pending",
  }));

  const doneStage: LiveStage = {
    label: "Done",
    state: status.overall_status === "complete" ? "done" : "pending",
  };

  return [uploadStage, ...stepStages, doneStage];
}

export function UploadPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const resumeIdParam = searchParams.get("resume");

  const [stage, setStage] = useState<Stage>(resumeIdParam ? "resuming" : "idle");
  const [uploadPercent, setUploadPercent] = useState(0);
  const [resume, setResume] = useState<Resume | null>(null);
  const [status, setStatus] = useState<ResumeProcessingStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, []);

  function startPolling(resumeId: string) {
    pollRef.current = window.setInterval(async () => {
      try {
        const latest = await resumeApi.getStatus(resumeId);
        setStatus(latest);
        if (latest.overall_status !== "in_progress") {
          setStage(latest.overall_status === "complete" ? "complete" : "failed");
          if (pollRef.current) window.clearInterval(pollRef.current);
        }
      } catch {
        // transient polling errors are ignored — the next tick retries
      }
    }, POLL_INTERVAL_MS);
  }

  // Resuming an in-flight (or already finished) resume from a dashboard link.
  useEffect(() => {
    if (!resumeIdParam) return;
    let cancelled = false;

    Promise.all([resumeApi.get(resumeIdParam), resumeApi.getStatus(resumeIdParam)])
      .then(([r, s]) => {
        if (cancelled) return;
        setResume(r);
        setStatus(s);
        if (s.overall_status === "in_progress") {
          setStage("processing");
          startPolling(resumeIdParam);
        } else {
          setStage(s.overall_status === "complete" ? "complete" : "failed");
        }
      })
      .catch(() => {
        if (cancelled) return;
        setError("We couldn't find that resume. It may have been removed.");
        setStage("idle");
        setSearchParams({}, { replace: true });
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resumeIdParam]);

  function reset() {
    setStage("idle");
    setResume(null);
    setStatus(null);
    setError(null);
    setSearchParams({}, { replace: true });
  }

  function handleFileSelected(file: File) {
    setError(null);
    setStage("uploading");
    setUploadPercent(0);

    resumeApi
      .upload(file, setUploadPercent)
      .then((created) => {
        setResume(created);
        setStage("processing");
        startPolling(created.id);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
        setStage("idle");
      });
  }

  const failedStep = status?.steps.find((s) => s.status === "failed");
  const stages = buildStages(stage, uploadPercent, status);
  const fileName = resume?.original_filename;

  return (
    <div className="mx-auto max-w-2xl px-8 py-8">
      <h1 className="text-xl font-semibold text-ink-900">New portfolio</h1>
      <p className="mt-1 text-sm text-ink-500">
        Upload a resume PDF and we&apos;ll extract, analyze, and generate your portfolio content.
      </p>

      <Card className="mt-6 p-6">
        {stage === "resuming" && (
          <div className="flex items-center gap-3 py-6">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink-300 border-t-ink-900" />
            <p className="text-sm text-ink-500">Loading your resume's progress…</p>
          </div>
        )}

        {stage === "idle" && <UploadDropzone onFileSelected={handleFileSelected} />}

        {stage === "idle" && error && (
          <div className="mt-4">
            <ErrorState
              problem="We couldn't upload that file."
              reason={error}
              fix="Make sure it's a PDF under the size limit, then try again."
            />
          </div>
        )}

        {(stage === "uploading" || stage === "processing" || stage === "complete" || stage === "failed") && (
          <div className="animate-fade-up">
            {fileName && (
              <p className="mb-6 text-sm font-medium text-ink-900">
                <span className="font-mono text-ink-500">{fileName}</span>
              </p>
            )}
            <LiveProcessingStrip stages={stages} />
            {stage === "uploading" && (
              <div className="mt-4">
                <ProgressBar percent={uploadPercent} />
              </div>
            )}
          </div>
        )}

        {stage === "complete" && (
          <div className="mt-6 rounded-md bg-accent-50 px-4 py-3 text-sm text-accent-700">
            Your portfolio website is ready. You can open it, switch themes, or download the files.
          </div>
        )}

        {stage === "failed" && (
          <div className="mt-6">
            <ErrorState
              problem="Something went wrong while processing this resume."
              reason={failedStep?.detail ?? "An unexpected error occurred during processing."}
              fix="Try uploading the file again. If it keeps failing, double-check it's a valid, text-based PDF."
            />
          </div>
        )}

        {/* One primary action per state — everything else is a quiet text link. */}
        {stage === "complete" && status?.portfolio_id && (
          <div className="mt-6 flex items-center gap-4">
            <Link to={`/portfolios/${status.portfolio_id}`}>
              <Button>View your portfolio</Button>
            </Link>
            <button onClick={reset} className="text-sm font-medium text-ink-500 hover:text-ink-900">
              Upload another resume
            </button>
          </div>
        )}

        {stage === "failed" && (
          <div className="mt-6 flex items-center gap-4">
            <Button onClick={reset}>Upload another resume</Button>
            <Link to="/dashboard" className="text-sm font-medium text-ink-500 hover:text-ink-900">
              Back to dashboard
            </Link>
          </div>
        )}
      </Card>
    </div>
  );
}

