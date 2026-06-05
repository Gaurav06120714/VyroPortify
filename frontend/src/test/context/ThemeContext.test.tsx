/**
 * Tests for ThemeContext (light-mode-only build).
 *
 * B7 rewrite — the original suite exercised setMode("dark") /
 * setMode("system") which were silently no-op'd in the light-only
 * commit. Tests passed, asserted nothing useful. This rewrite covers
 * the actual contract of the post-lock-down context: mode is always
 * "light", setMode is a no-op that doesn't break consumers, the
 * palette axis is the live knob, and persistence + html attributes
 * reflect that.
 */

import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";

import { ThemeProvider, useTheme, type Palette } from "@/context/ThemeContext";

function TestConsumer() {
  const { mode, resolved, isLight, setMode, palette, setPalette } = useTheme();
  return (
    <div>
      <span data-testid="mode">{mode}</span>
      <span data-testid="resolved">{resolved}</span>
      <span data-testid="is-light">{String(isLight)}</span>
      <span data-testid="palette">{palette}</span>
      <button data-testid="setmode-dark" onClick={() => setMode("dark")}>
        try dark
      </button>
      <button
        data-testid="set-palette-clarity"
        onClick={() => setPalette("clarity" as Palette)}
      >
        clarity
      </button>
      <button
        data-testid="set-palette-aurora"
        onClick={() => setPalette("aurora" as Palette)}
      >
        aurora
      </button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <ThemeProvider>
      <TestConsumer />
    </ThemeProvider>,
  );
}

describe("ThemeContext (light-only)", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    document.documentElement.removeAttribute("data-palette");
    document.documentElement.classList.remove("dark");
  });

  it("mode is permanently 'light'", () => {
    renderWithProvider();
    expect(screen.getByTestId("mode").textContent).toBe("light");
    expect(screen.getByTestId("resolved").textContent).toBe("light");
    expect(screen.getByTestId("is-light").textContent).toBe("true");
  });

  it("setMode is a no-op — calling setMode('dark') does not flip the theme", async () => {
    renderWithProvider();
    await act(async () => {
      screen.getByTestId("setmode-dark").click();
    });
    // Still light. The button click must not have changed anything.
    expect(screen.getByTestId("mode").textContent).toBe("light");
    expect(screen.getByTestId("resolved").textContent).toBe("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("data-theme attribute is always 'light' on documentElement", () => {
    renderWithProvider();
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("palette defaults to 'aurora'", () => {
    renderWithProvider();
    expect(screen.getByTestId("palette").textContent).toBe("aurora");
  });

  it("setPalette flips the palette + writes data-palette + persists", async () => {
    renderWithProvider();

    await act(async () => {
      screen.getByTestId("set-palette-clarity").click();
    });

    expect(screen.getByTestId("palette").textContent).toBe("clarity");
    expect(document.documentElement.getAttribute("data-palette")).toBe("clarity");
    expect(localStorage.getItem("portify-palette")).toBe("clarity");
  });

  it("loads saved palette from localStorage on mount", () => {
    localStorage.setItem("portify-palette", "clarity");
    renderWithProvider();
    expect(screen.getByTestId("palette").textContent).toBe("clarity");
  });

  it("setPalette('aurora') goes back to default", async () => {
    localStorage.setItem("portify-palette", "clarity");
    renderWithProvider();

    await act(async () => {
      screen.getByTestId("set-palette-aurora").click();
    });

    expect(screen.getByTestId("palette").textContent).toBe("aurora");
    expect(localStorage.getItem("portify-palette")).toBe("aurora");
  });

  it("legacy 'portify-theme=dark' in localStorage is migrated to 'light' on mount", () => {
    localStorage.setItem("portify-theme", "dark");
    renderWithProvider();
    expect(localStorage.getItem("portify-theme")).toBe("light");
  });
});
