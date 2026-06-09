"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { X } from "lucide-react";

interface Props {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  maxTags?: number;
}

export default function TagInput({
  tags,
  onChange,
  placeholder = "Type and press Enter…",
  maxTags = 30,
}: Props) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const add = (raw: string) => {
    const trimmed = raw.trim();
    if (!trimmed || tags.length >= maxTags) return;
    
    const pieces = trimmed.split(",").map((s) => s.trim()).filter(Boolean);
    const fresh = pieces.filter((p) => !tags.map((t) => t.toLowerCase()).includes(p.toLowerCase()));
    if (fresh.length) onChange([...tags, ...fresh]);
    setInput("");
  };

  const remove = (idx: number) => onChange(tags.filter((_, i) => i !== idx));

  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      add(input);
    } else if (e.key === "Backspace" && !input && tags.length) {
      remove(tags.length - 1);
    }
  };

  return (
    <div
      className="flex min-h-[52px] cursor-text flex-wrap gap-2 rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] p-3 focus-within:border-[var(--pf-accent)] transition-colors"
      onClick={() => inputRef.current?.focus()}
    >
      {tags.map((tag, i) => (
        <span
          key={i}
          className="flex items-center gap-1.5 rounded-lg bg-[var(--pf-accent-soft)] px-2.5 py-1 text-sm text-[var(--pf-accent-text)]"
        >
          {tag}
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); remove(i); }}
            className="text-[var(--pf-muted)] hover:text-[var(--pf-text)] transition-colors"
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}
      <input
        ref={inputRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={onKey}
        onBlur={() => input && add(input)}
        placeholder={tags.length === 0 ? placeholder : "Add more…"}
        className="min-w-[160px] flex-1 bg-transparent text-sm text-[var(--pf-text)] placeholder-[var(--pf-muted)] outline-none"
      />
    </div>
  );
}
