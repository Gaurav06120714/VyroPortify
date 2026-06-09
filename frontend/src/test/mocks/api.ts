import { vi } from "vitest";
import type { UploadResumeResponse } from "@/types";

export const mockUploadResume = vi.fn<() => Promise<UploadResumeResponse>>().mockResolvedValue({
  resume_id: "test-resume-id-001",
  filename: "test_resume.pdf",
  message: "Resume uploaded successfully",
});

export const mockGetResumes = vi.fn().mockResolvedValue({
  items: [],
  total: 0,
});

export const mockDeleteResume = vi.fn().mockResolvedValue(undefined);

export const mockGeneratePortfolio = vi.fn().mockResolvedValue({
  portfolio_id: "test-portfolio-id-001",
  job_queued: true,
  message: "Generation started",
});

export const mockGetPortfolioStatus = vi.fn().mockResolvedValue({
  id: "test-portfolio-id-001",
  status: "queued",
  html_url: null,
  slug: "test-user-slug-12345678",
  ai_fallback: false,
});

export const mockGetPortfolios = vi.fn().mockResolvedValue({
  items: [],
  total: 0,
});

export const mockPublishPortfolio = vi.fn().mockResolvedValue({
  id: "test-portfolio-id-001",
  is_public: true,
});

export const mockCreateCheckoutSession = vi.fn().mockResolvedValue({
  checkout_url: "https://checkout.stripe.com/pay/cs_test_mock",
  session_id: "cs_test_mock",
});

export const mockGetBillingStatus = vi.fn().mockResolvedValue({
  plan: "free",
  stripe_customer_id: null,
  subscription_status: null,
  current_period_end: null,
  cancel_at_period_end: null,
});

export const mockBuildResume = vi.fn().mockResolvedValue({
  resume_id: "built-resume-id-001",
  filename: "ai_resume.json",
  message: "Resume built successfully",
});

export const mockSuggestSkills = vi.fn().mockResolvedValue({
  suggestions: ["Docker", "Kubernetes", "AWS"],
});

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

export const apiMocks = {
  uploadResume: mockUploadResume,
  getResumes: mockGetResumes,
  deleteResume: mockDeleteResume,
  generatePortfolio: mockGeneratePortfolio,
  getPortfolioStatus: mockGetPortfolioStatus,
  getPortfolios: mockGetPortfolios,
  publishPortfolio: mockPublishPortfolio,
  createCheckoutSession: mockCreateCheckoutSession,
  getBillingStatus: mockGetBillingStatus,
  buildResume: mockBuildResume,
  suggestSkills: mockSuggestSkills,
  ApiError,
};
