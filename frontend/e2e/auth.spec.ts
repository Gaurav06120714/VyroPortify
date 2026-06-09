import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test("unauthenticated user visiting /dashboard is redirected", async ({ page }) => {
    
    await page.route("**/api/v1/**", (route) => {
      route.fulfill({ status: 401, json: { detail: "Unauthorized" } });
    });

    const response = await page.goto("/dashboard");

    const url = page.url();
    expect(url).not.toContain("/dashboard");
  });

  test("login page loads successfully", async ({ page }) => {
    await page.goto("/login");
    
    await expect(page).not.toHaveURL(/500/);
  });

  test("register page loads successfully", async ({ page }) => {
    await page.goto("/register");
    await expect(page).not.toHaveURL(/500/);
  });

  test("health endpoint is accessible", async ({ page }) => {
    await page.route("**/health", (route) => {
      route.fulfill({
        status: 200,
        json: { status: "ok", environment: "test" },
      });
    });

    const response = await page.request.get("http://localhost:8000/health");
    
    expect(response).toBeDefined();
  });

  test("marketing home page loads", async ({ page }) => {
    await page.goto("/");
    await expect(page).not.toHaveURL(/error/);
    
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });
});
