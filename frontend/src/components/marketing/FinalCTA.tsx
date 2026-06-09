"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function FinalCTA() {
  return (
    <section className="relative px-6 py-28">
      {}
      <div className="pointer-events-none absolute left-1/2 top-0 h-px w-3/4 -translate-x-1/2 bg-border" />

      <div className="relative mx-auto max-w-4xl text-center">
        <h2 className="text-5xl font-extrabold leading-[1.1] tracking-tight text-foreground sm:text-6xl lg:text-7xl">
          Your portfolio,<br />ready in 60 seconds
        </h2>

        <p className="mx-auto mt-6 max-w-xl text-lg text-muted-foreground">
          Upload your resume or answer 12 quick questions. Claude writes the copy, picks the layout, and hands you a live URL — usually before you&apos;ve finished reading this page.
        </p>

        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Link
            href="/register"
            className="group flex items-center gap-2 rounded-2xl bg-primary px-8 py-4 text-base font-semibold text-primary-foreground transition-all hover:bg-primary/90"
          >
            Build my portfolio free
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
        <p className="mt-4 text-sm text-muted-foreground/60">
          Free forever · No credit card · Live in 60 seconds
        </p>
      </div>
    </section>
  );
}
