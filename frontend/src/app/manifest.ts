import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "VyroPortify — AI Portfolio Generator",
    short_name: "VyroPortify",
    description:
      "Turn your resume into a stunning hosted portfolio in under 60 seconds.",
    start_url: "/?source=pwa",
    scope: "/",
    display: "standalone",
    // v2.2.1 — Clarity-palette colors so the install splash matches
    // the light-mode-only build that landed in v1.7.
    background_color: "#ffffff",
    theme_color: "#2563eb",
    orientation: "portrait",
    categories: ["productivity", "business"],
    // Shortcuts surface deep links from the home-screen long-press menu.
    shortcuts: [
      {
        name: "Builder",
        short_name: "Builder",
        url: "/dashboard/builder/new",
        description: "Open the unified portfolio builder",
      },
      {
        name: "Marketplace",
        short_name: "Marketplace",
        url: "/dashboard/marketplace",
        description: "Browse community templates",
      },
    ],
    icons: [
      {
        src: "/favicon.ico",
        sizes: "any",
        type: "image/x-icon",
      },
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
