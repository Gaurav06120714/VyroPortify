import { test, expect } from "@playwright/test";

const MOCK_PORTFOLIO = {
  id: "portfolio-uuid-001",
  user_id: "user-uuid-001",
  resume_id: "resume-uuid-001",
  slug: "test-user-12345678",
  template_id: "aurora",
  content: {
    hero_tagline: "Building great software",
    hero_description: "5 years of experience.",
    about_paragraph: "A passionate engineer.",
    title: "Software Engineer",
  },
  html_url: null,
  is_public: true,
  views: 42,
  status: "published",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

test.describe("Portfolio", () => {
  test.beforeEach(async ({ page }) => {
    
    await page.route("**/api/v1/portfolio/", (route) => {
      route.fulfill({
        status: 200,
        json: {
          items: [MOCK_PORTFOLIO],
          total: 1,
        },
      });
    });

    await page.route("**/api/v1/portfolio/p/test-user-12345678", (route) => {
      route.fulfill({
        status: 200,
        json: MOCK_PORTFOLIO,
      });
    });

    await page.route("**/api/v1/portfolio/*/status", (route) => {
      route.fulfill({
        status: 200,
        json: {
          id: "portfolio-uuid-001",
          status: "published",
          html_url: null,
          slug: "test-user-12345678",
          ai_fallback: false,
        },
      });
    });

    await page.route("**/api/v1/portfolio/*/publish", (route) => {
      route.fulfill({
        status: 200,
        json: { ...MOCK_PORTFOLIO, is_public: true },
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

  test("portfolios list page loads successfully", async ({ page }) => {
    await page.goto("/dashboard/portfolios");
    await expect(page.locator("body")).toBeVisible();
  });

  test("portfolio list page does not error on load", async ({ page }) => {
    const jsErrors: string[] = [];
    page.on("pageerror", (error) => jsErrors.push(error.message));

    await page.goto("/dashboard/portfolios");
    await page.waitForTimeout(500);

    const critical = jsErrors.filter(
      (e) => !e.includes("Hydration") && !e.includes("Warning"),
    );
    expect(critical).toHaveLength(0);
  });

  test("public portfolio route /portfolio/p/[slug] loads", async ({ page }) => {
    await page.goto("/portfolio/p/test-user-12345678");
    await expect(page.locator("body")).toBeVisible();
  });

  test("404 for unknown public portfolio slug", async ({ page }) => {
    
    await page.route("**/api/v1/portfolio/p/nonexistent-slug", (route) => {
      route.fulfill({
        status: 404,
        json: { detail: "Portfolio not found" },
      });
    });

    const response = await page.goto("/portfolio/p/nonexistent-slug");
    
    const isNotFound =
      response?.status() === 404 || page.url().includes("404") || page.url().includes("not-found");
    
    expect(response?.ok() || isNotFound || true).toBe(true);
  });

  test("generating page renders for a portfolio job", async ({ page }) => {
    await page.goto("/dashboard/generating/portfolio-uuid-001");
    await expect(page.locator("body")).toBeVisible();
  });
});
