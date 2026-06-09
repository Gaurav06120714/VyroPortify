import { notFound } from "next/navigation";
import type { Metadata } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://vyroportify.com";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001/api/v1";

interface PortfolioData {
  id: string;
  slug: string;
  status: string;
  is_public: boolean;
  html_url: string | null;
  views: number;
  content?: {
    full_name?: string;
    title?: string;
    summary?: string;
    avatar_url?: string;
  } | null;
}

async function fetchPortfolio(slug: string): Promise<PortfolioData | null> {
  try {
    const res = await fetch(`${API_URL}/portfolio/p/${slug}`, {
      next: { revalidate: 3600 }, 
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const portfolio = await fetchPortfolio(slug);

  const name = portfolio?.content?.full_name ?? slug;
  const title = portfolio?.content?.title ?? "Developer";
  const summary = portfolio?.content?.summary;
  const avatarUrl = portfolio?.content?.avatar_url;

  const ogTitle = `${name} — ${title}`;
  const ogDesc = summary
    ? summary.slice(0, 160)
    : `View ${name}'s AI-generated portfolio. Built with VyroPortify.`;

  return {
    title: `${name} · Portfolio`,
    description: ogDesc,
    openGraph: {
      title: ogTitle,
      description: ogDesc,
      url: `${BASE_URL}/portfolio/${slug}`,
      type: "profile",
      siteName: "VyroPortify",
      images: avatarUrl
        ? [{ url: avatarUrl, width: 400, height: 400, alt: name }]
        : [
            {
              url: `${BASE_URL}/og-default.png`,
              width: 1200,
              height: 630,
              alt: "VyroPortify — AI Portfolio Generator",
            },
          ],
    },
    twitter: {
      card: "summary_large_image",
      title: ogTitle,
      description: ogDesc,
      images: avatarUrl ? [avatarUrl] : [`${BASE_URL}/og-default.png`],
    },
    alternates: {
      canonical: `${BASE_URL}/portfolio/${slug}`,
    },
  };
}

export default async function PublicPortfolioPage({ params }: Props) {
  const { slug } = await params;
  const portfolio = await fetchPortfolio(slug);

  if (!portfolio || !portfolio.is_public || portfolio.status !== "published") {
    notFound();
  }

  if (portfolio.html_url) {
    return (
      <iframe
        src={portfolio.html_url}
        className="fixed inset-0 h-full w-full border-0"
        title={`${portfolio.content?.full_name ?? slug}'s portfolio`}
        sandbox="allow-scripts allow-same-origin"
      />
    );
  }

  notFound();
}
