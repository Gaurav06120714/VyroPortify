import type { Metadata } from "next";
import { notFound } from "next/navigation";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3007";

interface Props {
  params: Promise<{ slug: string }>;
}

// Social-card metadata. Next.js auto-wires the sibling opengraph-image.tsx
// as the og image for this route, so we don't repeat the URL here.
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
    /* defaults */
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
    return res.json() as Promise<{ html_url: string | null; status: string }>;
  } catch {
    return null;
  }
}

export default async function PublicPortfolioPage({ params }: Props) {
  const { slug } = await params;
  const portfolio = await fetchPortfolio(slug);

  if (!portfolio || portfolio.status !== "published" || !portfolio.html_url) {
    notFound();
  }

  // Proxy-render the HTML via an iframe pointed at the S3 URL
  return (
    <iframe
      src={portfolio.html_url}
      className="h-dvh w-full border-0"
      title="Portfolio"
      sandbox="allow-scripts allow-same-origin"
    />
  );
}
