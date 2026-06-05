import type {
  Resume,
  Portfolio,
  PortfolioStatus,
  UploadResumeResponse,
  GeneratePortfolioResponse,
  PaginatedResponse,
  BuildResumeRequest,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001/api/v1";

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {},
): Promise<T> {
  const { token, ...init } = options;
  const headers = new Headers(init.headers);

  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      const raw = body.detail ?? detail;
      // Pydantic validation errors come back as an array of objects — flatten to string
      if (Array.isArray(raw)) {
        detail = raw.map((e: { msg?: string; loc?: string[] }) =>
          [e.loc?.slice(1).join("."), e.msg].filter(Boolean).join(": ")
        ).join("; ");
      } else {
        detail = String(raw);
      }
    } catch {}
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ─── Resume ────────────────────────────────────────────────────────────────

export async function uploadResume(
  file: File,
  token: string,
): Promise<UploadResumeResponse> {
  const form = new FormData();
  form.append("file", file);
  return request<UploadResumeResponse>("/resume/upload", {
    method: "POST",
    body: form,
    token,
  });
}

export async function getResumes(
  token: string,
  page = 1,
  size = 20,
): Promise<PaginatedResponse<Resume>> {
  return request<PaginatedResponse<Resume>>(
    `/resume/?page=${page}&size=${size}`,
    { token },
  );
}

export async function getResume(id: string, token: string): Promise<Resume> {
  return request<Resume>(`/resume/${id}`, { token });
}

export async function deleteResume(id: string, token: string): Promise<void> {
  return request<void>(`/resume/${id}`, { method: "DELETE", token });
}

// ─── Portfolio ─────────────────────────────────────────────────────────────

export async function generatePortfolio(
  resumeId: string,
  templateId: "aurora" | "minimal" | "cyber" | "executive",
  token: string,
): Promise<GeneratePortfolioResponse> {
  return request<GeneratePortfolioResponse>("/portfolio/generate", {
    method: "POST",
    body: JSON.stringify({ resume_id: resumeId, template_id: templateId }),
    token,
  });
}

export async function getPortfolios(
  token: string,
  page = 1,
  size = 20,
): Promise<PaginatedResponse<Portfolio>> {
  return request<PaginatedResponse<Portfolio>>(
    `/portfolio/?page=${page}&size=${size}`,
    { token },
  );
}

export async function getPortfolioStatus(
  id: string,
  token: string,
): Promise<PortfolioStatus> {
  return request<PortfolioStatus>(`/portfolio/${id}/status`, { token });
}

export async function publishPortfolio(
  id: string,
  token: string,
): Promise<Portfolio> {
  return request<Portfolio>(`/portfolio/${id}/publish`, {
    method: "PUT",
    token,
  });
}

export async function deletePortfolio(id: string, token: string): Promise<void> {
  return request<void>(`/portfolio/${id}`, { method: "DELETE", token });
}

// ─── Resume Builder ────────────────────────────────────────────────────────

export async function buildResume(
  data: BuildResumeRequest,
  token: string,
): Promise<UploadResumeResponse> {
  return request<UploadResumeResponse>("/resume/build", {
    method: "POST",
    body: JSON.stringify(data),
    token,
  });
}

export async function generateCoverLetter(
  payload: {
    name: string;
    title: string;
    company: string;
    role: string;
    highlights: string;
    tone: string;
  },
  token: string,
): Promise<{ cover_letter: string }> {
  return request<{ cover_letter: string }>("/resume/cover-letter", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export async function suggestSkills(
  payload: {
    current_skills: string[];
    tech_stack: string[];
    role_titles: string[];
    career_goal: string;
  },
  token: string,
): Promise<{ suggestions: string[] }> {
  return request<{ suggestions: string[] }>("/resume/suggest-skills", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

// ─── Billing ───────────────────────────────────────────────────────────────

export async function createCheckoutSession(
  token: string,
): Promise<{ checkout_url: string; session_id: string }> {
  return request("/billing/create-checkout", { method: "POST", token });
}

export async function getBillingStatus(token: string): Promise<{
  plan: string;
  stripe_customer_id: string | null;
  subscription_status: string | null;
  current_period_end: number | null;
  cancel_at_period_end: boolean | null;
}> {
  return request("/billing/status", { token });
}

export async function getPortalUrl(
  token: string,
): Promise<{ portal_url: string }> {
  return request("/billing/portal", { token });
}

export { ApiError };
