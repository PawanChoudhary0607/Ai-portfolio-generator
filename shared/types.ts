/**
 * Shared API contract types.
 *
 * These mirror the backend's Pydantic schemas one-for-one (see
 * backend/app/schemas/*.py). Keeping them in `shared/` rather than inside
 * `frontend/` is what makes this a contract both sides are written
 * against, instead of the frontend silently drifting from whatever the
 * backend happens to return. If a backend DTO changes, update it here
 * first.
 */

// ── Auth ─────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface MessageResponse {
  message: string;
}

// ── Resumes ──────────────────────────────────────────────────────────────

export type ResumeStatus =
  | "uploaded"
  | "extracting"
  | "extracted"
  | "analyzing"
  | "analyzed"
  | "failed";

export interface Resume {
  id: string;
  original_filename: string;
  file_size_bytes: number;
  status: ResumeStatus;
  failure_reason: string | null;
  page_count: number | null;
  created_at: string;
  updated_at: string;
}

export type PipelineStepStatus = "pending" | "in_progress" | "complete" | "failed";

export interface ResumeProcessingStep {
  key: "extraction" | "ai_analysis" | "portfolio_generation" | "website_generation";
  label: string;
  status: PipelineStepStatus;
  detail: string | null;
}

export interface ResumeProcessingStatus {
  resume_id: string;
  overall_status: "in_progress" | "complete" | "failed";
  steps: ResumeProcessingStep[];
  portfolio_id: string | null;
}

// ── Portfolios ───────────────────────────────────────────────────────────

export type PortfolioStatus = "generating" | "draft" | "published" | "failed";

export interface Portfolio {
  id: string;
  resume_id: string;
  title: string;
  status: PortfolioStatus;
  failure_reason: string | null;
  selected_theme: string | null;
  created_at: string;
  updated_at: string;
}

export interface Theme {
  value: string;
  label: string;
  description: string;
}

export interface PortfolioDetail extends Portfolio {
  // Mirrors the engine's PortfolioSchema, minus internal fields the
  // backend strips before this ever reaches the client (e.g. llm_model).
  portfolio_schema_json: Record<string, unknown> | null;
}

// ── Dashboard ────────────────────────────────────────────────────────────

export interface DashboardResumeSummary {
  id: string;
  original_filename: string;
  status: ResumeStatus;
  created_at: string;
}

export interface DashboardPortfolioSummary {
  id: string;
  title: string;
  status: PortfolioStatus;
  selected_theme: string | null;
  updated_at: string;
}

export interface DashboardPublishedSiteSummary {
  id: string;
  portfolio_id: string;
  slug: string;
  is_active: boolean;
  published_at: string;
}

export interface DashboardVersionSummary {
  id: string;
  portfolio_id: string;
  version_number: number;
  created_at: string;
}

export interface DashboardOverview {
  recent_resumes: DashboardResumeSummary[];
  generated_portfolios: DashboardPortfolioSummary[];
  published_sites: DashboardPublishedSiteSummary[];
  drafts: DashboardPortfolioSummary[];
  version_history: DashboardVersionSummary[];
}

// ── Constants ────────────────────────────────────────────────────────────

export const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB — keep in sync with backend Settings.MAX_UPLOAD_SIZE_BYTES
export const ALLOWED_UPLOAD_MIME_TYPES = ["application/pdf"];
