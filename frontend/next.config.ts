import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow images from common avatar and CDN sources
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "img.clerk.com" },
      { protocol: "https", hostname: "images.clerk.dev" },
      { protocol: "https", hostname: "avatars.githubusercontent.com" },
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
      { protocol: "https", hostname: "portifyai.s3.amazonaws.com" },
      { protocol: "https", hostname: "*.s3.amazonaws.com" },
    ],
  },

  // Security headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-DNS-Prefetch-Control", value: "on" },
          { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },

  // Proxy API calls to backend in development
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },

  // Source maps in production:
  // - Server-side source maps are SAFE (never sent to the browser).
  // - Browser source maps EXPOSE your source code to anyone opening DevTools.
  //   Only enable if you use Sentry's hidden-source-map upload (which deletes
  //   the public .map files after uploading). Default: off.
  productionBrowserSourceMaps: false,

  // Strict mode for catching bugs early
  reactStrictMode: true,

  // Ignore ESLint errors during production builds (CI handles lint separately)
  eslint: {
    ignoreDuringBuilds: true,
  },

  // Ignore TypeScript errors during production builds (CI handles tsc separately)
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
