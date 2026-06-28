import type {
  DashboardOverview,
  MessageResponse,
  Portfolio,
  PortfolioDetail,
  Resume,
  ResumeProcessingStatus,
  Theme,
  TokenResponse,
} from "@shared/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
const REQUEST_TIMEOUT_MS = 15000;

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  return localStorage.getItem("access_token");
}

export function setToken(token: string | null): void {
  if (token) {
    localStorage.setItem("access_token", token);
  } else {
    localStorage.removeItem("access_token");
  }
}

function withAuthHeaders(options: RequestInit = {}): Headers {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && options.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

function timeoutSignal(ms = REQUEST_TIMEOUT_MS): AbortSignal {
  const controller = new AbortController();
  window.setTimeout(() => controller.abort(), ms);
  return controller.signal;
}

function friendlyDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: unknown } | undefined;
    if (typeof first?.msg === "string") return first.msg;
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === "string") return message;
  }
  return fallback;
}

async function readError(response: Response): Promise<ApiError> {
  let detail = response.statusText;
  try {
    const body = await response.json();
    detail = friendlyDetail(body.detail, detail);
  } catch {
    // The response had no JSON body.
  }
  return new ApiError(response.status, detail);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: withAuthHeaders(options),
      signal: options.signal ?? timeoutSignal(),
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, "The request took too long. Please try again.");
    }
    throw new ApiError(0, "We couldn't reach the server. Please check your connection.");
  }

  if (!response.ok) {
    throw await readError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function requestText(path: string, options: RequestInit = {}): Promise<string> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: withAuthHeaders(options),
      signal: options.signal ?? timeoutSignal(),
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, "The request took too long. Please try again.");
    }
    throw new ApiError(0, "We couldn't reach the server. Please check your connection.");
  }
  if (!response.ok) {
    throw await readError(response);
  }
  return response.text();
}

async function requestBlob(path: string): Promise<Blob> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: withAuthHeaders(),
      signal: timeoutSignal(30000),
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, "The download took too long. Please try again.");
    }
    throw new ApiError(0, "We couldn't reach the server. Please check your connection.");
  }
  if (!response.ok) {
    throw await readError(response);
  }
  return response.blob();
}

export const authApi = {
  signUp: (email: string, password: string, full_name: string) =>
    request<TokenResponse>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),

  logIn: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<TokenResponse["user"]>("/auth/me"),

  forgotPassword: (email: string) =>
    request<MessageResponse>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  resetPassword: (token: string, new_password: string) =>
    request<MessageResponse>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password }),
    }),
};

export const resumeApi = {
  upload: (file: File, onProgress?: (pct: number) => void) =>
    uploadWithProgress(file, onProgress),

  list: () => request<Resume[]>("/resumes"),

  get: (id: string) => request<Resume>(`/resumes/${id}`),

  getStatus: (id: string) => request<ResumeProcessingStatus>(`/resumes/${id}/status`),
};

function uploadWithProgress(file: File, onProgress?: (pct: number) => void): Promise<Resume> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}/resumes`);
    const token = getToken();
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        let detail = xhr.statusText;
        try {
          detail = JSON.parse(xhr.responseText).detail ?? detail;
        } catch {
          // Keep status text.
        }
        reject(new ApiError(xhr.status, detail));
      }
    };
    xhr.onerror = () => reject(new ApiError(0, "Network error during upload"));
    xhr.send(formData);
  });
}

export const portfolioApi = {
  list: () => request<Portfolio[]>("/portfolios"),
  get: (id: string) => request<PortfolioDetail>(`/portfolios/${id}`),
  themeCatalog: () => request<Theme[]>("/portfolios/themes/catalog"),
  demoWebsite: (theme: string) => requestText(`/portfolios/themes/${theme}/demo-website`),
  previewTheme: (portfolioId: string, theme: string) =>
    request<{ html: string; theme: string }>(`/portfolios/${portfolioId}/theme-preview`, {
      method: "POST",
      body: JSON.stringify({ theme }),
    }),
  websiteHtml: (portfolioId: string, theme?: string) =>
    requestText(`/portfolios/${portfolioId}/website${theme ? `?theme=${encodeURIComponent(theme)}` : ""}`),
  exportHtml: (portfolioId: string, theme?: string) =>
    requestBlob(`/portfolios/${portfolioId}/export/html${theme ? `?theme=${encodeURIComponent(theme)}` : ""}`),
  exportZip: (portfolioId: string, theme?: string) =>
    requestBlob(`/portfolios/${portfolioId}/export/zip${theme ? `?theme=${encodeURIComponent(theme)}` : ""}`),
};

export const dashboardApi = {
  overview: () => request<DashboardOverview>("/dashboard/overview"),
};
