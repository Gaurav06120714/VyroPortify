"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";

type ThemeMode = "light" | "dark" | "system";
type ResolvedTheme = "light" | "dark";
// v1.7.0: palette is an independent axis from light/dark.
// "aurora" = original purple/violet palette (default).
// "clarity" = Gridlock-inspired blue + warm-amber civic-modern palette.
export type Palette = "aurora" | "clarity";

interface ThemeContextValue {
  mode: ThemeMode;
  resolved: ResolvedTheme;
  setMode: (mode: ThemeMode) => void;
  isLight: boolean;
  palette: Palette;
  setPalette: (p: Palette) => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  mode: "light",
  resolved: "light",
  setMode: () => {},
  isLight: true,
  palette: "aurora",
  setPalette: () => {},
});

function getSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

const PALETTE_KEY = "portify-palette";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>("dark");
  const [resolved, setResolved] = useState<ResolvedTheme>("dark");
  const [palette, setPaletteState] = useState<Palette>("aurora");

  // Load saved preferences
  useEffect(() => {
    const saved = localStorage.getItem("portify-theme") as ThemeMode | null;
    if (saved && ["light", "dark", "system"].includes(saved)) {
      setModeState(saved);
    }
    const savedPalette = localStorage.getItem(PALETTE_KEY) as Palette | null;
    if (savedPalette === "clarity" || savedPalette === "aurora") {
      setPaletteState(savedPalette);
    }
  }, []);

  // Resolve theme and listen for system changes
  useEffect(() => {
    const r = mode === "system" ? getSystemTheme() : mode;
    setResolved(r);

    // Apply to <html> for global CSS access
    document.documentElement.setAttribute("data-theme", r);
    document.documentElement.classList.toggle("dark", r === "dark");

    if (mode === "system") {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      const handler = (e: MediaQueryListEvent) => {
        const newTheme = e.matches ? "dark" : "light";
        setResolved(newTheme);
        document.documentElement.setAttribute("data-theme", newTheme);
        document.documentElement.classList.toggle("dark", newTheme === "dark");
      };
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    }
  }, [mode]);

  // Apply palette to <html>. Independent axis from light/dark.
  useEffect(() => {
    document.documentElement.setAttribute("data-palette", palette);
  }, [palette]);

  const setMode = useCallback((m: ThemeMode) => {
    setModeState(m);
    localStorage.setItem("portify-theme", m);
  }, []);

  const setPalette = useCallback((p: Palette) => {
    setPaletteState(p);
    localStorage.setItem(PALETTE_KEY, p);
  }, []);

  return (
    <ThemeContext.Provider
      value={{
        mode,
        resolved,
        setMode,
        isLight: resolved === "light",
        palette,
        setPalette,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
