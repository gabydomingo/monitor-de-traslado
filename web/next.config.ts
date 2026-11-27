import type { NextConfig } from "next";

// sitio estatico: next build deja todo en out/ y vercel lo sirve tal cual
const config: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  trailingSlash: true,
};

export default config;
