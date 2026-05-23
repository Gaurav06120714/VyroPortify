import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "VyroPortify — AI Portfolio Generator",
    short_name: "VyroPortify",
    description:
      "Turn your resume into a stunning hosted portfolio in under 60 seconds.",
    start_url: "/",
    display: "standalone",
    background_color: "#0d0d14",
    theme_color: "#6c63ff",
    orientation: "portrait",
    categories: ["productivity", "business"],
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
