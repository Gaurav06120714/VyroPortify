import type { Metadata } from "next";
import { notFound } from "next/navigation";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001/api/v1";
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3007";

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  let title = "Portfolio · VyroPortify";
  let description = "An AI-generated portfolio on VyroPortify.";
  try {
    const res = await fetch(`${BASE_URL}/portfolio/p/${slug}`, {
      next: { revalidate: 300 },
    });
    if (res.ok) {
      const data = (await res.json()) as {
        content?: { full_name?: string; title?: string };
      };
      if (data.content?.full_name) title = `${data.content.full_name} · VyroPortify`;
      if (data.content?.title) description = data.content.title;
    }
  } catch {
    
  }
  const url = `${SITE_URL}/portfolio/p/${slug}`;
  return {
    title,
    description,
    openGraph: { title, description, url, type: "profile" },
    twitter: { card: "summary_large_image", title, description },
    alternates: { canonical: url },
  };
}

async function fetchPortfolio(slug: string) {
  try {
    const res = await fetch(`${BASE_URL}/portfolio/p/${slug}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    return res.json() as Promise<{
      html_url: string | null;
      status: string;
      content: PortfolioContent | null;
      template_id: string | null;
    }>;
  } catch {
    return null;
  }
}

interface PortfolioContent {
  full_name?: string;
  title?: string;
  summary?: string;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  work_experience?: Array<{
    company?: string;
    role?: string;
    start?: string;
    end?: string;
    bullets?: string[];
    achievements?: string;
  }>;
  education?: Array<{ degree?: string; institution?: string; year?: string }>;
  skills?: string[];
  projects?: Array<{ name?: string; description?: string; tech?: string[]; link?: string }>;
  links?: { github?: string; linkedin?: string; website?: string };
}

export default async function PublicPortfolioPage({ params }: Props) {
  const { slug } = await params;
  const portfolio = await fetchPortfolio(slug);

  if (!portfolio || portfolio.status !== "published") {
    notFound();
  }

  if (portfolio.html_url) {
    return (
      <iframe
        src={portfolio.html_url}
        className="h-dvh w-full border-0"
        title="Portfolio"
        sandbox="allow-scripts allow-same-origin"
      />
    );
  }

  const c: PortfolioContent = portfolio.content ?? {};
  return (
    <main className="mx-auto max-w-3xl px-6 py-16 text-[var(--pf-text)]">
      <header className="mb-10 border-b border-[var(--pf-border-light)] pb-6">
        <h1 className="text-h1 text-[var(--pf-text)]">
          {c.full_name ?? "Portfolio"}
        </h1>
        {c.title && (
          <p className="mt-1 text-lg text-[var(--pf-muted)]">{c.title}</p>
        )}
        {(c.email || c.phone || c.location) && (
          <p className="mt-3 text-sm text-[var(--pf-muted)]">
            {[c.email, c.phone, c.location].filter(Boolean).join(" · ")}
          </p>
        )}
      </header>

      {c.summary && (
        <Section title="Summary">
          <p className="whitespace-pre-line text-[var(--pf-text-dim)]">
            {c.summary}
          </p>
        </Section>
      )}

      {c.work_experience && c.work_experience.length > 0 && (
        <Section title="Experience">
          {c.work_experience.map((job, i) => (
            <div key={i} className="mb-5">
              <div className="flex items-baseline justify-between">
                <p className="font-semibold">
                  {job.role}
                  {job.company ? ` · ${job.company}` : ""}
                </p>
                {(job.start || job.end) && (
                  <span className="text-xs text-[var(--pf-muted)]">
                    {job.start} – {job.end || "Present"}
                  </span>
                )}
              </div>
              {job.bullets && job.bullets.length > 0 ? (
                <ul className="mt-1 list-inside list-disc text-[var(--pf-text-dim)]">
                  {job.bullets.map((b, j) => <li key={j}>{b}</li>)}
                </ul>
              ) : (
                job.achievements && (
                  <p className="mt-1 whitespace-pre-line text-[var(--pf-text-dim)]">
                    {job.achievements}
                  </p>
                )
              )}
            </div>
          ))}
        </Section>
      )}

      {c.projects && c.projects.length > 0 && (
        <Section title="Projects">
          {c.projects.map((p, i) => (
            <div key={i} className="mb-4">
              <p className="font-semibold">
                {p.name}
                {p.link && (
                  <a
                    href={p.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 text-sm text-[var(--pf-accent)] underline"
                  >
                    link
                  </a>
                )}
              </p>
              {p.description && (
                <p className="text-[var(--pf-text-dim)]">{p.description}</p>
              )}
              {p.tech && p.tech.length > 0 && (
                <p className="mt-1 text-xs text-[var(--pf-muted)]">
                  {p.tech.join(" · ")}
                </p>
              )}
            </div>
          ))}
        </Section>
      )}

      {c.education && c.education.length > 0 && (
        <Section title="Education">
          {c.education.map((ed, i) => (
            <p key={i} className="text-[var(--pf-text-dim)]">
              <span className="font-semibold">{ed.degree}</span>
              {ed.institution && ` · ${ed.institution}`}
              {ed.year && ` · ${ed.year}`}
            </p>
          ))}
        </Section>
      )}

      {c.skills && c.skills.length > 0 && (
        <Section title="Skills">
          <p className="text-[var(--pf-text-dim)]">{c.skills.join(" · ")}</p>
        </Section>
      )}

      {c.links && (c.links.github || c.links.linkedin || c.links.website) && (
        <Section title="Links">
          <ul className="space-y-1">
            {c.links.github && <li><a href={c.links.github} className="text-[var(--pf-accent)] underline" target="_blank" rel="noopener noreferrer">GitHub</a></li>}
            {c.links.linkedin && <li><a href={c.links.linkedin} className="text-[var(--pf-accent)] underline" target="_blank" rel="noopener noreferrer">LinkedIn</a></li>}
            {c.links.website && <li><a href={c.links.website} className="text-[var(--pf-accent)] underline" target="_blank" rel="noopener noreferrer">Website</a></li>}
          </ul>
        </Section>
      )}

      <footer className="mt-16 border-t border-[var(--pf-border-light)] pt-4 text-center text-xs text-[var(--pf-muted)]">
        Made with VyroPortify
      </footer>
    </main>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-8">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--pf-accent)]">
        {title}
      </h2>
      {children}
    </section>
  );
}
