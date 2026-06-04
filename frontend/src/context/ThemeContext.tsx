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
  // Light-mode-only build (Jun 2026). The mode state is preserved so the
  // public API of useTheme() doesn't break for existing consumers, but
  // setMode is now a no-op and the resolved theme is permanently "light".
  // The palette axis (Aurora vs Clarity) is still user-selectable.
  const [mode] = useState<ThemeMode>("light");
  const [resolved] = useState<ResolvedTheme>("light");
  const [palette, setPaletteState] = useState<Palette>("aurora");

  // Load saved palette preference. Theme mode is intentionally not loaded
  // from storage anymore — light is the only allowed value.
  useEffect(() => {
    const savedPalette = localStorage.getItem(PALETTE_KEY) as Palette | null;
    if (savedPalette === "clarity" || savedPalette === "aurora") {
      setPaletteState(savedPalette);
    }
    // Defensively clear any stale value users might have set in the past
    // so existing browsers don't keep forcing dark via cached storage.
    try {
      localStorage.setItem("portify-theme", "light");
    } catch {
      /* ignore */
    }
  }, []);

  // Hard-pin light mode on <html> every render so nothing else can flip it.
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", "light");
    document.documentElement.classList.remove("dark");
  }, []);

  // Apply palette to <html>. Independent axis from light/dark.
  useEffect(() => {
    document.documentElement.setAttribute("data-palette", palette);
  }, [palette]);

  // No-op: light-only build. Kept on the context so consumers compile.
  const setMode = useCallback((_m: ThemeMode) => {
    /* intentionally no-op */
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
