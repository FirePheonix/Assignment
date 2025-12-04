import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
      {
        protocol: "http",
        hostname: "127.0.0.1",
      },
      {
        protocol: "http",
        hostname: "localhost",
      },
    ],
  },
  // Note: serverActions config was moved to experimental in Next.js 15
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb', // Increase limit for base64 images from Django
    },
  },
  // API routes now handle Django proxy with fallback, no need for rewrites
};

export default nextConfig;
