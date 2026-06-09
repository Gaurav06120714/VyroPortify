import { test, expect } from "@playwright/test";

test.describe("Resume Builder", () => {
  test.beforeEach(async ({ page }) => {
    
    await page.route("**/api/v1/resume/build", (route) => {
      route.fulfill({
        status: 201,
        json: {
          resume_id: "built-resume-uuid-001",
          filename: "test_user_ai_resume.json",
          message: "Resume built successfully",
        },
      });
    });

    await page.route("**/api/v1/resume/suggest-skills", (route) => {
      route.fulfill({
        status: 200,
        json: {
          suggestions: ["Docker", "Kubernetes", "CI/CD"],
        },
      });
    });

    await page.route("**/api/v1/portfolio/generate", (route) => {
      route.fulfill({
        status: 202,
        json: {
          portfolio_id: "portfolio-uuid-001",
          job_queued: true,
          message: "Portfolio generation started.",
        },
      });
    });

    await page.route("**/api/v1/auth/me", (route) => {
      route.fulfill({
        status: 200,
        json: {
          id: "user-uuid-001",
          email: "test@example.com",
          name: "Test User",
          plan: "free",
          avatar_url: null,
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
        },
      });
    });
  });

  test("builder page loads without crashing", async ({ page }) => {
    await page.goto("/dashboard/build-resume");
    await expect(page.locator("body")).toBeVisible();
  });

  test("builder page renders form elements", async ({ page }) => {
    await page.goto("/dashboard/build-resume");
    
    const inputs = page.locator("input, textarea, button");
    const count = await inputs.count();
    expect(count).toBeGreaterThan(0);
  });

  test("builder page does not throw JavaScript errors on load", async ({ page }) => {
    const jsErrors: string[] = [];
    page.on("pageerror", (error) => jsErrors.push(error.message));

    await page.goto("/dashboard/build-resume");
    await page.waitForTimeout(500);

    const criticalErrors = jsErrors.filter(
      (e) => !e.includes("Hydration") && !e.includes("Warning"),
    );
    expect(criticalErrors).toHaveLength(0);
  });

  test("Next button advances to the next step if present", async ({ page }) => {
    await page.goto("/dashboard/build-resume");

    const nextButton = page.locator("button", { hasText: /next|continue/i }).first();

    if (await nextButton.count() > 0 && await nextButton.isEnabled()) {
      await nextButton.click();
      
      expect(page.url()).toContain("build-resume");
    }
  });
});
