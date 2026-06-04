import { ImageResponse } from "next/og";

// OG image generator — Next.js renders this on-the-fly at /portfolio/p/<slug>/opengraph-image.
// 1200x630 is the social-card standard (Twitter, LinkedIn, Facebook all accept it).
// Edge runtime keeps cold-start fast and avoids pulling Node-only deps.

export const runtime = "edge";
export const alt = "VyroPortify";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

interface PortfolioMeta {
  full_name?: string;
  title?: string;
  status?: string;
}

async function fetchMeta(slug: string): Promise<PortfolioMeta | null> {
  try {
    const res = await fetch(`${BASE_URL}/portfolio/p/${slug}`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return null;
    const data = (await res.json()) as {
      content?: { full_name?: string; title?: string };
      status?: string;
    };
    return {
      full_name: data.content?.full_name,
      title: data.content?.title,
      status: data.status,
    };
  } catch {
    return null;
  }
}

export default async function OgImage({ params }: { params: { slug: string } }) {
  const meta = await fetchMeta(params.slug);
  const name = (meta?.full_name ?? "VyroPortify").slice(0, 60);
  const title = (meta?.title ?? "Portfolio").slice(0, 80);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "80px",
          background:
            "linear-gradient(135deg, #0a0a14 0%, #1a1a2e 50%, #2d1b4e 100%)",
          color: "#ffffff",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div
            style={{
              width: "20px",
              height: "20px",
              borderRadius: "999px",
              background: "#7c5cff",
              boxShadow: "0 0 32px #7c5cff",
            }}
          />
          <span
            style={{
              fontSize: "28px",
              fontWeight: 700,
              letterSpacing: "-0.02em",
            }}
          >
            VyroPortify
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <span
            style={{
              fontSize: "84px",
              fontWeight: 800,
              lineHeight: 1.05,
              letterSpacing: "-0.04em",
              maxWidth: "1000px",
            }}
          >
            {name}
          </span>
          <span
            style={{
              fontSize: "36px",
              fontWeight: 500,
              color: "#a89cd9",
              letterSpacing: "-0.01em",
            }}
          >
            {title}
          </span>
        </div>

        <span style={{ fontSize: "22px", color: "#9999bb" }}>
          vyroportify.com / portfolio
        </span>
      </div>
    ),
    { ...size },
  );
}
