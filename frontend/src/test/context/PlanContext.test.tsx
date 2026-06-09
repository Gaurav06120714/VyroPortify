import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act, waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react";

const mockGetToken = vi.fn().mockResolvedValue("mock-token");
const mockIsSignedIn = vi.fn(() => true);

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    isSignedIn: mockIsSignedIn(),
    isLoaded: true,
    getToken: mockGetToken,
  }),
}));

const mockGetBillingStatus = vi.fn();

vi.mock("@/lib/api", () => ({
  getBillingStatus: (...args: any[]) => mockGetBillingStatus(...args),
}));

import { PlanProvider, usePlan } from "@/context/PlanContext";

function TestConsumer() {
  const { plan, loading, refresh } = usePlan();
  return (
    <div>
      <span data-testid="plan">{plan}</span>
      <span data-testid="loading">{String(loading)}</span>
      <button data-testid="refresh" onClick={() => refresh()}>
        Refresh
      </button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <PlanProvider>
      <TestConsumer />
    </PlanProvider>,
  );
}

describe("PlanContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsSignedIn.mockReturnValue(true);
  });

  it("provides 'free' plan by default before API call", () => {
    mockGetBillingStatus.mockResolvedValue({ plan: "free" });
    renderWithProvider();
    
    expect(screen.getByTestId("plan").textContent).toBe("free");
  });

  it("shows loading=true initially when signed in", () => {
    mockGetBillingStatus.mockImplementation(
      () => new Promise(() => {}), 
    );
    renderWithProvider();
    expect(screen.getByTestId("loading").textContent).toBe("true");
  });

  it("sets loading=false after API call completes", async () => {
    mockGetBillingStatus.mockResolvedValue({ plan: "free" });
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
    });
  });

  it("updates plan to 'pro' when API returns pro", async () => {
    mockGetBillingStatus.mockResolvedValue({ plan: "pro" });
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("plan").textContent).toBe("pro");
    });
  });

  it("keeps 'free' plan when API returns unknown plan", async () => {
    mockGetBillingStatus.mockResolvedValue({ plan: "unknown_plan" });
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("plan").textContent).toBe("free");
    });
  });

  it("keeps 'free' plan when API throws an error", async () => {
    mockGetBillingStatus.mockRejectedValue(new Error("API error"));
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
    });
    expect(screen.getByTestId("plan").textContent).toBe("free");
  });

  it("does not call API when user is not signed in", async () => {
    mockIsSignedIn.mockReturnValue(false);
    mockGetBillingStatus.mockResolvedValue({ plan: "pro" });
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
    });
    expect(mockGetBillingStatus).not.toHaveBeenCalled();
  });

  it("refresh() re-fetches billing status", async () => {
    mockGetBillingStatus
      .mockResolvedValueOnce({ plan: "free" })
      .mockResolvedValueOnce({ plan: "pro" });

    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("plan").textContent).toBe("free");
    });

    await act(async () => {
      screen.getByTestId("refresh").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("plan").textContent).toBe("pro");
    });

    expect(mockGetBillingStatus).toHaveBeenCalledTimes(2);
  });

  it("usePlan hook returns context values", () => {
    mockGetBillingStatus.mockResolvedValue({ plan: "free" });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <PlanProvider>{children}</PlanProvider>
    );
    const { result } = renderHook(() => usePlan(), { wrapper });

    expect(result.current.plan).toBe("free");
    expect(typeof result.current.loading).toBe("boolean");
    expect(typeof result.current.refresh).toBe("function");
  });
});
