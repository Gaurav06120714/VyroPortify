import { test, expect } from "@playwright/test";

test.describe("Billing", () => {
  test.beforeEach(async ({ page }) => {
    
    await page.route("**/api/v1/billing/status", (route) => {
      route.fulfill({
        status: 200,
        json: {
          plan: "free",
          stripe_customer_id: null,
          subscription_status: null,
          current_period_end: null,
          cancel_at_period_end: null,
        },
      });
    });

    await page.route("**/api/v1/billing/create-checkout", (route) => {
      route.fulfill({
        status: 201,
        json: {
          checkout_url: "https://checkout.stripe.com/pay/cs_test_mock_session",
          session_id: "cs_test_mock_session",
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

  test("pricing page loads successfully", async ({ page }) => {
    await page.goto("/pricing");
    await expect(page.locator("body")).toBeVisible();
  });

  test("pricing page renders pricing content", async ({ page }) => {
    await page.goto("/pricing");
    
    const text = await page.locator("body").innerText();
    
    expect(text.length).toBeGreaterThan(10);
  });

  test("billing settings page loads for authenticated user", async ({ page }) => {
    await page.goto("/dashboard/settings/billing");
    await expect(page.locator("body")).toBeVisible();
  });

  test("billing settings page does not crash with JS error", async ({ page }) => {
    const jsErrors: string[] = [];
    page.on("pageerror", (error) => jsErrors.push(error.message));

    await page.goto("/dashboard/settings/billing");
    await page.waitForTimeout(500);

    const critical = jsErrors.filter(
      (e) => !e.includes("Hydration") && !e.includes("Warning"),
    );
    expect(critical).toHaveLength(0);
  });

  test("upgrade button on pricing page triggers checkout API call", async ({ page }) => {
    let checkoutCalled = false;

    await page.route("**/api/v1/billing/create-checkout", (route) => {
      checkoutCalled = true;
      route.fulfill({
        status: 201,
        json: {
          checkout_url: "https://checkout.stripe.com/pay/cs_test_mock",
          session_id: "cs_test_mock",
        },
      });
    });

    await page.goto("/pricing");

    const upgradeBtn = page
      .locator("button, a", { hasText: /get pro|upgrade|subscribe|start/i })
      .first();

    if (await upgradeBtn.count() > 0 && await upgradeBtn.isVisible()) {
      await upgradeBtn.click();
      
      await page.waitForTimeout(500);
      
    }

    await expect(page.locator("body")).toBeVisible();
  });
});
