"use client";

import { motion } from "framer-motion";
import { ArrowRight, FileText, CheckCircle2, Globe } from "lucide-react";
import FadeUp from "./FadeUp";

const RAW_RESUME = `Alex Johnson
Software Engineer · San Francisco

EXPERIENCE
Senior Engineer, Acme Corp  2022–present
- worked on backend
- fixed production bugs
- helped junior devs

Engineer, StartupXYZ  2019–2022
- built some React stuff
- wrote Python scripts

EDUCATION
BS Computer Science, UC Davis  2019

SKILLS
React, Python, Node, AWS`;

const PORTFOLIO_SECTIONS = [
  {
    label: "Headline",
    before: "Senior Engineer, Acme Corp",
    after: "Senior Software Engineer building distributed systems that handle 40M+ requests/day",
  },
  {
    label: "Bio",
    before: "worked on backend, fixed production bugs",
    after: "5 years building backend infrastructure at scale. Led a team of 4 engineers through a zero-downtime migration from monolith to microservices. Reduced p99 latency by 62%.",
  },
  {
    label: "Skills",
    before: "React, Python, Node, AWS",
    after: "React · TypeScript · Python · Node.js · AWS (EC2, RDS, SQS) · PostgreSQL · Redis · Docker · Terraform",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="relative px-6 py-28">
      <div className="mx-auto max-w-6xl">
        <FadeUp className="mb-16 text-center">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-primary">
            How it works
          </div>
          <h2 className="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl">
            This is what actually happens
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
            You paste your resume. Claude rewrites it into portfolio copy. Here&apos;s a real example.
          </p>
        </FadeUp>

        {/* Before / After */}
        <FadeUp delay={0.1}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start mb-10">

            {/* Before — raw resume */}
            <div className="rounded-2xl border border-border bg-card overflow-hidden">
              <div className="flex items-center gap-2 px-5 py-3 border-b border-border bg-muted/20">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-semibold text-muted-foreground">Your resume (before)</span>
              </div>
              <pre className="px-5 py-4 font-mono text-[12px] leading-relaxed text-muted-foreground/70 whitespace-pre-wrap overflow-auto max-h-64">
                {RAW_RESUME}
              </pre>
            </div>

            {/* After — generated portfolio copy */}
            <div className="rounded-2xl border border-primary/30 bg-card overflow-hidden">
              <div className="flex items-center gap-2 px-5 py-3 border-b border-primary/20 bg-primary/5">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <span className="text-sm font-semibold text-primary">What Claude generates</span>
              </div>
              <div className="divide-y divide-border">
                {PORTFOLIO_SECTIONS.map(({ label, before, after }) => (
                  <div key={label} className="px-5 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/50 mb-2">{label}</div>
                    <div className="flex flex-col gap-2">
                      <div className="flex gap-2 items-start">
                        <span className="text-[10px] font-semibold text-muted-foreground/40 w-10 shrink-0 pt-0.5">before</span>
                        <span className="text-[12px] text-muted-foreground/50 line-through leading-relaxed">{before}</span>
                      </div>
                      <div className="flex gap-2 items-start">
                        <span className="text-[10px] font-semibold text-primary/70 w-10 shrink-0 pt-0.5">after</span>
                        <span className="text-[12px] text-foreground leading-relaxed">{after}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </FadeUp>

        {/* Steps strip — condensed below the before/after */}
        <FadeUp delay={0.2}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { n: "01", title: "Paste your resume", body: "Upload a PDF or fill out 12 questions. Takes under 5 minutes." },
              { n: "02", title: "Claude rewrites it", body: "Gets your headline, bio, bullet points, and skills — all in one pass." },
              { n: "03", title: "Pick a template, go live", body: "Choose Aurora, Minimal, or Cyber. Your URL is ready in under 60 seconds." },
            ].map(({ n, title, body }) => (
              <div key={n} className="flex gap-4 items-start rounded-2xl border border-border bg-card p-5">
                <span className="font-mono text-3xl font-extrabold text-primary/20 leading-none shrink-0">{n}</span>
                <div>
                  <div className="font-semibold text-foreground mb-1">{title}</div>
                  <p className="text-sm text-muted-foreground leading-relaxed">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </FadeUp>
      </div>
    </section>
  );
}
