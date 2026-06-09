import Navbar from "@/components/marketing/Navbar";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  
  return (
    <div className="min-h-dvh bg-[var(--pf-bg)] text-[var(--pf-text)]">
      <Navbar />
      {children}
    </div>
  );
}
