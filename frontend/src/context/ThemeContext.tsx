"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";

type ThemeMode = "light" | "dark" | "system";
type ResolvedTheme = "light" | "dark";

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
  
  const [mode] = useState<ThemeMode>("light");
  const [resolved] = useState<ResolvedTheme>("light");
  const [palette, setPaletteState] = useState<Palette>("aurora");

  useEffect(() => {
    const savedPalette = localStorage.getItem(PALETTE_KEY) as Palette | null;
    if (savedPalette === "clarity" || savedPalette === "aurora") {
      setPaletteState(savedPalette);
    }
    
    try {
      localStorage.setItem("portify-theme", "light");
    } catch {
      
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", "light");
    document.documentElement.classList.remove("dark");
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-palette", palette);
  }, [palette]);

  const setMode = useCallback((_m: ThemeMode) => {
    
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
