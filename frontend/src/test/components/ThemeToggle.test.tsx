import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

vi.mock("lucide-react", () => ({
  Sun: () => <span data-testid="icon-sun">☀️</span>,
  Moon: () => <span data-testid="icon-moon">🌙</span>,
  Monitor: () => <span data-testid="icon-monitor">🖥️</span>,
  ChevronDown: () => <span>▼</span>,
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

import { ThemeProvider } from "@/context/ThemeContext";
import ThemeToggle from "@/components/ThemeToggle";

function renderWithTheme() {
  return render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>,
  );
}

describe("ThemeToggle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    localStorage.clear();
    
    document.documentElement.removeAttribute("data-theme");
    document.documentElement.classList.remove("dark");
  });

  it("renders without crashing", () => {
    renderWithTheme();
    
    expect(document.body.children.length).toBeGreaterThan(0);
  });

  it.skip("renders a clickable toggle element", () => {
    
    renderWithTheme();
    const buttons = document.querySelectorAll("button");
    expect(buttons.length).toBeGreaterThan(0);
  });
});
