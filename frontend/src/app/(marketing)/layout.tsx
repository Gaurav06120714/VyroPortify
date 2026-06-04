import Navbar from "@/components/marketing/Navbar";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  // Was hardcoded bg-[#0F0F1A] (deep dark navy) — that's what kept
  // forcing the marketing surface dark on top of the light palette.
  // Switched to the --pf-bg token so it follows whichever palette is
  // active (Aurora light or Clarity white).
  return (
    <div className="min-h-dvh bg-[var(--pf-bg)] text-[var(--pf-text)]">
      <Navbar />
      {children}
    </div>
  );
}
