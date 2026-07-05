import type { NextConfig } from "next";

const internalApiOrigin =
  process.env.INTERNAL_API_ORIGIN || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/health/:path*",
        destination: `${internalApiOrigin}/health/:path*`,
      },
      {
        source: "/connections/:path*",
        destination: `${internalApiOrigin}/connections/:path*`,
      },
      {
        source: "/pipeline/:path*",
        destination: `${internalApiOrigin}/pipeline/:path*`,
      },
      {
        source: "/conversations/:path*",
        destination: `${internalApiOrigin}/conversations/:path*`,
      },
      {
        source: "/docs",
        destination: `${internalApiOrigin}/docs`,
      },
      {
        source: "/docs/:path*",
        destination: `${internalApiOrigin}/docs/:path*`,
      },
      {
        source: "/redoc",
        destination: `${internalApiOrigin}/redoc`,
      },
      {
        source: "/openapi.json",
        destination: `${internalApiOrigin}/openapi.json`,
      },
    ];
  },
};

export default nextConfig;
