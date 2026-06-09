"use client";

import FadeUp from "./FadeUp";

const COMPANIES: { name: string; url: string }[] = [
  { name: "Stripe", url: "https://stripe.com" },
  { name: "Vercel", url: "https://vercel.com" },
  { name: "Linear", url: "https://linear.app" },
  { name: "Figma", url: "https://figma.com" },
  { name: "Notion", url: "https://notion.so" },
  { name: "GitHub", url: "https://github.com" },
  { name: "Shopify", url: "https://shopify.com" },
  { name: "Airbnb", url: "https://airbnb.com" },
  { name: "Spotify", url: "https://spotify.com" },
  { name: "Twilio", url: "https://twilio.com" },
  { name: "Slack", url: "https://slack.com" },
  { name: "Atlassian", url: "https://atlassian.com" },
  { name: "Netflix", url: "https://netflix.com" },
  { name: "Uber", url: "https://uber.com" },
  { name: "Meta", url: "https://meta.com" },
  { name: "Google", url: "https://google.com" },
  { name: "Apple", url: "https://apple.com" },
  { name: "Microsoft", url: "https://microsoft.com" },
  { name: "Amazon", url: "https://amazon.com" },
  { name: "Tesla", url: "https://tesla.com" },
];

function LogoChip({ name, url }: { name: string; url: string }) {
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex h-9 items-center justify-center rounded-xl border border-border bg-muted/20 px-6 text-sm font-bold tracking-wide text-muted-foreground/60 transition-colors hover:border-primary/30 hover:text-muted-foreground"
    >
      {name}
    </a>
  );
}

export default function LogoBar() {
  const doubled = [...COMPANIES, ...COMPANIES];

  return (
    <section className="border-y border-border bg-muted/10 py-12">
      <FadeUp className="mb-7 text-center text-sm font-bold uppercase tracking-widest text-muted-foreground/50">
        Used by people at
      </FadeUp>

      <div className="relative overflow-hidden">
        {}
        <div className="pointer-events-none absolute left-0 top-0 z-10 h-full w-24 bg-gradient-to-r from-background to-transparent" />
        {}
        <div className="pointer-events-none absolute right-0 top-0 z-10 h-full w-24 bg-gradient-to-l from-background to-transparent" />

        <div className="flex gap-4 animate-marquee" style={{ width: "max-content" }}>
          {doubled.map((company, i) => (
            <LogoChip key={i} name={company.name} url={company.url} />
          ))}
        </div>
      </div>
    </section>
  );
}
