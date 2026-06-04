import Sidebar from "@/components/dashboard/Sidebar";
import MobileHeader from "@/components/dashboard/MobileHeader";
import { MobileBindings } from "@/components/dashboard/MobileBindings";
import PageTransition from "@/components/PageTransition";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-dvh bg-[var(--pf-bg)]">
      <div className="hidden lg:flex lg:flex-shrink-0">
        <Sidebar />
      </div>

      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        <MobileHeader />
        {/* v2.2.2 — pb-20 on mobile so the fixed BottomTabNav doesn't
            overlap content; lg restores the original 6 unit padding. */}
        <main className="flex-1 overflow-y-auto p-6 pb-20 lg:pb-6">
          <PageTransition>{children}</PageTransition>
        </main>
      </div>

      {/* v2.2.2 — bottom tab nav + swipe-back gesture (mobile only). */}
      <MobileBindings />
    </div>
  );
}
