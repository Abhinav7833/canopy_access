import type { NextConfig } from "next";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8001";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND_URL}/:path*` },
      { source: "/static/:path*", destination: `${BACKEND_URL}/static/:path*` },
    ];
  },
};

export default nextConfig;
