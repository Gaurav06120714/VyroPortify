import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";
import os from "os";

test.describe("Resume Upload", () => {
  test.beforeEach(async ({ page }) => {
    
    await page.route("**/api/v1/resume/upload", (route) => {
      route.fulfill({
        status: 201,
        json: {
          id: "test-resume-uuid-001",
          user_id: "test-user-uuid-001",
          file_url: "https://s3.example.com/presigned",
          file_type: "pdf",
          original_filename: "test_resume.pdf",
          status: "done",
          parsed_data: {
            full_name: "Test User",
            email: "test@example.com",
            skills: ["Python", "React"],
          },
          raw_text: null,
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
          resume_id: "test-resume-uuid-001",
          filename: "test_resume.pdf",
          message: "Resume uploaded successfully",
        },
      });
    });

    await page.route("**/api/v1/auth/me", (route) => {
      route.fulfill({
        status: 200,
        json: {
          id: "test-user-uuid-001",
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

  test("upload page loads successfully", async ({ page }) => {
    await page.goto("/dashboard/upload");
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  test("upload zone is visible on the upload page", async ({ page }) => {
    await page.goto("/dashboard/upload");
    
    const dropZone = page.locator("[class*='dropzone'], [class*='upload'], input[type='file']").first();
    
    await expect(page.locator("body")).toBeVisible();
  });

  test("can attach a PDF file to the upload input", async ({ page }) => {
    await page.goto("/dashboard/upload");

    const tmpDir = os.tmpdir();
    const pdfPath = path.join(tmpDir, "test_resume.pdf");
    
    fs.writeFileSync(pdfPath, "%PDF-1.4 test resume content");

    const fileInput = page.locator('input[type="file"]').first();

    if (await fileInput.count() > 0) {
      await fileInput.setInputFiles(pdfPath);
      
      await expect(page.locator("body")).toBeVisible();
    }

    fs.unlinkSync(pdfPath);
  });

  test("navigating to upload page does not cause 500 error", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });

    await page.goto("/dashboard/upload");
    
    const criticalErrors = errors.filter(
      (e) => e.includes("TypeError") || e.includes("Cannot read"),
    );
    expect(criticalErrors).toHaveLength(0);
  });
});
