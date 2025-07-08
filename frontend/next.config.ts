import type { NextConfig } from "next";

// Allow running the app behind a reverse proxy by reading the base path
// from an environment variable. Both `basePath` and `assetPrefix` must be
// configured so all assets resolve correctly when the application isn't
// served from the root URL.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

const nextConfig: NextConfig = {
  basePath,
  assetPrefix: basePath,
};

export default nextConfig;
