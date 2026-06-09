"use client";

import { useTheme, type Palette } from "@/context/ThemeContext";
import { cn } from "@/lib/utils";

const OPTIONS: { value: Palette; label: string; hint: string }[] = [
  { value: "aurora", label: "Aurora", hint: "Dark violet · default" },
  { value: "clarity", label: "Clarity", hint: "Light blue · clean" },
];

export function PaletteToggle({ className }: { className?: string }) {
  const { palette, setPalette } = useTheme();

  return (
    <fieldset className={cn("space-y-2", className)}>
      <legend className="text-sm font-medium text-[var(--pf-text)]">
        Color palette
      </legend>
      <div className="grid grid-cols-2 gap-2">
        {OPTIONS.map((opt) => {
          const selected = palette === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => setPalette(opt.value)}
              className={cn(
                "flex flex-col items-start gap-1 rounded-xl border p-3 text-left transition-colors",
                selected
                  ? "border-[var(--pf-accent)] bg-[var(--pf-accent-subtle)]"
                  : "border-[var(--pf-border-light)] hover:bg-[var(--pf-surface2)]",
              )}
            >
              <span className="text-sm font-semibold text-[var(--pf-text)]">
                {opt.label}
              </span>
              <span className="text-xs text-[var(--pf-muted)]">{opt.hint}</span>
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
