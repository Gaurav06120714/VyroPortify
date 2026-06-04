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
          {/* Anti-flash: resolve theme + palette before React hydrates so
              CSS variables are correct on the very first paint. v1.7.0
              extends the original script to also apply data-palette. */}
          <script dangerouslySetInnerHTML={{ __html: `try{var t=localStorage.getItem('portify-theme')||'dark';var r=t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;document.documentElement.setAttribute('data-theme',r);document.documentElement.classList.toggle('dark',r==='dark');var p=localStorage.getItem('portify-palette');if(p==='clarity'||p==='aurora'){document.documentElement.setAttribute('data-palette',p)}else{document.documentElement.setAttribute('data-palette','aurora')}}catch(e){document.documentElement.classList.add('dark');document.documentElement.setAttribute('data-palette','aurora')}` }} />
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
