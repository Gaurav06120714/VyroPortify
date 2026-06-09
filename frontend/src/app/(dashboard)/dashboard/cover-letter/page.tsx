"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { Sparkles, Copy, Check, RefreshCw, FileText } from "lucide-react";
import { generateCoverLetter, ApiError } from "@/lib/api";

const TONE_OPTIONS = [
  { value: "professional", label: "Professional", desc: "Polished & formal" },
  { value: "enthusiastic", label: "Enthusiastic", desc: "Energetic & passionate" },
  { value: "concise", label: "Concise", desc: "Brief & direct" },
] as const;

type Tone = (typeof TONE_OPTIONS)[number]["value"];

export default function CoverLetterPage() {
  const { getToken } = useAuth();

  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [highlights, setHighlights] = useState("");
  const [tone, setTone] = useState<Tone>("professional");
  const [letter, setLetter] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    if (!name.trim() || !company.trim() || !role.trim()) {
      toast.error("Please fill in your name, target company, and role.");
      return;
    }
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const res = await generateCoverLetter({ name, title, company, role, highlights, tone }, token);
      setLetter(res.cover_letter);
      toast.success("Cover letter generated!");
    } catch (err) {
      
      if (err instanceof ApiError && err.status === 403) {
        toast.error("Cover letter requires the Pro plan.", {
          description: "Upgrade in Settings → Billing to use AI cover letters.",
          duration: 7000,
        });
      } else if (err instanceof ApiError) {
        toast.error(err.detail || "Generation failed. Please try again.");
      } else {
        toast.error("Generation failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(letter);
    setCopied(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--pf-accent-soft)]">
            <FileText className="h-5 w-5 text-[var(--pf-accent)]" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[var(--pf-text)]">Cover Letter Generator</h1>
            <p className="text-sm text-[var(--pf-muted)]">Claude writes a tailored cover letter in seconds</p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05, duration: 0.3 }}
          className="space-y-4 rounded-xl border border-[var(--pf-accent-soft)] bg-[var(--pf-surface)] p-6"
        >
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--pf-muted)]">Your Details</h2>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Your Name *" value={name} onChange={setName} placeholder="Alex Johnson" />
            <Field label="Your Title" value={title} onChange={setTitle} placeholder="Full-Stack Engineer" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Target Company *" value={company} onChange={setCompany} placeholder="Stripe" />
            <Field label="Target Role *" value={role} onChange={setRole} placeholder="Senior Engineer" />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-[var(--pf-muted)]">
              Key Highlights
              <span className="ml-1 text-[var(--pf-muted-dim)]">(achievements, skills to emphasise)</span>
            </label>
            <textarea
              value={highlights}
              onChange={(e) => setHighlights(e.target.value)}
              placeholder="Led migration to microservices reducing latency 40%. Built payment API handling $2M/day. 5 years TypeScript, 3 years Go."
              rows={4}
              className="w-full resize-none rounded-lg border border-[var(--pf-border-light)] bg-[var(--pf-bg)] px-3 py-2.5 text-sm text-[var(--pf-text)] placeholder:text-[var(--pf-muted-darker)] focus:border-[var(--pf-accent)] focus:outline-none transition-colors"
            />
          </div>

          {}
          <div>
            <label className="mb-2 block text-xs font-medium text-[var(--pf-muted)]">Tone</label>
            <div className="grid grid-cols-3 gap-2">
              {TONE_OPTIONS.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setTone(t.value)}
                  className={`rounded-lg border px-3 py-2 text-left transition-colors ${
                    tone === t.value
                      ? "border-[var(--pf-accent)] bg-[var(--pf-accent-subtle)] text-[var(--pf-accent-text)]"
                      : "border-[var(--pf-accent-soft)] text-[var(--pf-muted)] hover:border-[rgba(108,99,255,0.35)]"
                  }`}
                >
                  <p className="text-xs font-semibold">{t.label}</p>
                  <p className="text-[10px] opacity-70">{t.desc}</p>
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--pf-accent)] px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-[var(--pf-accent-hover)] disabled:opacity-60"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Generating…
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Generate Cover Letter
              </>
            )}
          </button>
        </motion.div>

        {}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.3 }}
          className="flex flex-col rounded-xl border border-[var(--pf-accent-soft)] bg-[var(--pf-surface)]"
        >
          <div className="flex items-center justify-between border-b border-[var(--pf-border-dim)] px-5 py-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--pf-muted)]">Output</h2>
            {letter && (
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-[var(--pf-muted)] hover:bg-[var(--pf-border-subtle)] hover:text-[var(--pf-text)] transition-colors"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? "Copied!" : "Copy"}
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-5">
            {letter ? (
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--pf-text-dim)]">{letter}</p>
            ) : (
              <div className="flex h-full min-h-[300px] flex-col items-center justify-center gap-3 text-center">
                <Sparkles className="h-8 w-8 text-[var(--pf-muted-darkest)]" />
                <p className="text-sm text-[var(--pf-muted-dim)]">
                  Fill in the details on the left<br />and click Generate.
                </p>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-[var(--pf-muted)]">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-[var(--pf-border-light)] bg-[var(--pf-bg)] px-3 py-2.5 text-sm text-[var(--pf-text)] placeholder:text-[var(--pf-muted-darker)] focus:border-[var(--pf-accent)] focus:outline-none transition-colors"
      />
    </div>
  );
}
