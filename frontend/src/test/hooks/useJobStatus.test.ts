import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    isSignedIn: true,
    isLoaded: true,
    getToken: vi.fn().mockResolvedValue("mock-token"),
  }),
}));

const mockGetPortfolioStatus = vi.fn();

vi.mock("@/lib/api", () => ({
  getPortfolioStatus: (...args: unknown[]) => mockGetPortfolioStatus(...args),
}));

import { useJobStatus } from "@/hooks/useJobStatus";

const JOB_ID = "portfolio-job-123";

describe("useJobStatus", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("starts with 'parsing' phase and null error", () => {
    
    mockGetPortfolioStatus.mockReturnValue(new Promise(() => {})); 

    const { result, unmount } = renderHook(() => useJobStatus(JOB_ID));

    expect(result.current.phase).toBe("parsing");
    expect(result.current.error).toBeNull();
    expect(result.current.portfolioStatus).toBeNull();

    unmount();
  });

  it("calls getPortfolioStatus with the correct jobId and token", async () => {
    mockGetPortfolioStatus.mockResolvedValue({
      id: JOB_ID,
      status: "queued",
      html_url: null,
      slug: "test-slug",
      ai_fallback: false,
    });

    const { unmount } = renderHook(() => useJobStatus(JOB_ID));

    await act(async () => {
      
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(mockGetPortfolioStatus).toHaveBeenCalledWith(JOB_ID, "mock-token");

    unmount();
  });

  it("sets portfolioStatus after a successful poll", async () => {
    mockGetPortfolioStatus.mockResolvedValue({
      id: JOB_ID,
      status: "queued",
      html_url: null,
      slug: "test-slug",
      ai_fallback: false,
    });

    const { result, unmount } = renderHook(() => useJobStatus(JOB_ID));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(result.current.portfolioStatus).not.toBeNull();
    expect(result.current.portfolioStatus?.status).toBe("queued");

    unmount();
  });

  it("sets phase=done when status is 'published'", async () => {
    mockGetPortfolioStatus.mockResolvedValue({
      id: JOB_ID,
      status: "published",
      html_url: "https://portify.ai/p/test-slug",
      slug: "test-slug",
      ai_fallback: false,
    });

    const { result, unmount } = renderHook(() => useJobStatus(JOB_ID));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(result.current.phase).toBe("done");

    unmount();
  });

  it("sets phase=failed and error message when status is 'failed'", async () => {
    mockGetPortfolioStatus.mockResolvedValue({
      id: JOB_ID,
      status: "failed",
      html_url: null,
      slug: "test-slug",
      ai_fallback: false,
    });

    const { result, unmount } = renderHook(() => useJobStatus(JOB_ID));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(result.current.phase).toBe("failed");
    expect(result.current.error).not.toBeNull();

    unmount();
  });

  it("handles fetch error gracefully without crashing", async () => {
    mockGetPortfolioStatus.mockRejectedValue(new Error("Network error"));

    const { result, unmount } = renderHook(() => useJobStatus(JOB_ID));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(result.current.phase).toBe("parsing");
    
    expect(result.current.error).toBeNull();

    unmount();
  });

  it("stops making API calls after unmount", async () => {
    mockGetPortfolioStatus.mockResolvedValue({
      id: JOB_ID,
      status: "queued",
      html_url: null,
      slug: "test-slug",
      ai_fallback: false,
    });

    const { unmount } = renderHook(() => useJobStatus(JOB_ID));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 100));
    });

    const countBeforeUnmount = mockGetPortfolioStatus.mock.calls.length;

    unmount();

    await new Promise((r) => setTimeout(r, 200));

    expect(mockGetPortfolioStatus.mock.calls.length).toBe(countBeforeUnmount);
  }, 10_000);
});
