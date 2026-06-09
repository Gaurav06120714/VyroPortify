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
        {}
        <main className="flex-1 overflow-y-auto p-6 pb-20 lg:pb-6">
          <PageTransition>{children}</PageTransition>
        </main>
      </div>

      {}
      <MobileBindings />
    </div>
  );
}
