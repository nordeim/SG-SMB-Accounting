import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * LEDGERSG NAVIGATION TESTS
 *
 * Purpose: Verify basic navigation and page structure
 * Coverage: All public routes, accessibility checks
 */

test.describe("Navigation", () => {
  test("landing page loads successfully", async ({ page }) => {
    await page.goto("/");

    // Verify page title
    await expect(page).toHaveTitle(/LedgerSG/);

    // Verify main content exists
    await expect(page.locator("text=LedgerSG").first()).toBeVisible();
  });

  test("login page is accessible", async ({ page }) => {
    await page.goto("/login");

    // Verify login form elements
    await expect(page.locator("input[type='email']")).toBeVisible();
    await expect(page.locator("input[type='password']")).toBeVisible();
    await expect(page.locator("button[type='submit']")).toBeVisible();
  });

  test("404 page is shown for unknown routes", async ({ page }) => {
    await page.goto("/nonexistent-page");

    // Verify 404 content
    await expect(page.locator("text=404")).toBeVisible();
    await expect(page.locator("text=Page Not Found")).toBeVisible();

    // Verify navigation options
    await expect(page.locator("text=Go to Dashboard")).toBeVisible();
  });

  test("landing page passes accessibility scan", async ({ page }) => {
    await page.goto("/");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .exclude("[data-testid='axe-exclude']")
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});

test.describe("Responsive Design", () => {
  test("navigation adapts to mobile viewport", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto("/");

    // Verify content is visible and accessible
    await expect(page.locator("text=LedgerSG").first()).toBeVisible();
  });

  test("navigation adapts to tablet viewport", async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    await page.goto("/");

    // Verify content is visible and accessible
    await expect(page.locator("text=LedgerSG").first()).toBeVisible();
  });
});
