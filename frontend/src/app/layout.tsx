import type { Metadata } from "next";
import { Inter, Geist_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { Toaster } from "sonner";
import { PlanProvider } from "@/context/PlanContext";
import { ThemeProvider } from "@/context/ThemeContext";
import Providers from "@/components/Providers";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "VyroPortify — AI Portfolio Generator",
  description: "Transform your resume into a beautiful portfolio in under 60 seconds.",
  openGraph: {
    title: "VyroPortify — AI Portfolio Generator",
    description: "Transform your resume into a beautiful portfolio in under 60 seconds.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider
      afterSignOutUrl="/"
      signInUrl="/login"
      signUpUrl="/register"
    >
      <html lang="en" suppressHydrationWarning>
        <head>
          {/* Pre-hydration palette resolver. Theme is locked to "light"
              (light-mode-only build, Jun 2026), so only the palette axis
              is resolved here. */}
          <script dangerouslySetInnerHTML={{ __html: `try{document.documentElement.setAttribute('data-theme','light');document.documentElement.classList.remove('dark');var p=localStorage.getItem('portify-palette');document.documentElement.setAttribute('data-palette',(p==='clarity'||p==='aurora')?p:'aurora')}catch(e){document.documentElement.setAttribute('data-theme','light');document.documentElement.setAttribute('data-palette','aurora')}` }} />
        </head>
        <body
          className={`${inter.variable} ${geistMono.variable} antialiased`}
        >
          <ThemeProvider>
            <Providers>
              <PlanProvider>{children}</PlanProvider>
            </Providers>
          </ThemeProvider>
          <Toaster
            position="bottom-right"
            toastOptions={{
              className: "portify-toast",
            }}
          />
        </body>
      </html>
    </ClerkProvider>
  );
}
