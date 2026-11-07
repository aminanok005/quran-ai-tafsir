module.exports = {
  reactStrictMode: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  eslint: {
    dirs: ["src"],
  },
  images: {
    domains: [
      "localhost",
      "api.quran.foundation",
      "cdn.quran.foundation"
    ],
  },
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ["@headlessui/react", "lucide-react"],
  },
  i18n: {
    locales: ["th", "ar", "en"],
    defaultLocale: "th",
  },
  headers: async () => [
    {
      source: "/_next/static/:path*",
      headers: [
        {
          key: "Cache-Control",
          value: "public, max-age=31536000, immutable",
        },
      ],
    },
    {
      source: "/api/quran/:path*",
      headers: [
        {
          key: "Cache-Control",
          value: "public, max-age=3600, stale-while-revalidate=86400",
        },
      ],
    },
  ],
  webpack: (config, { isServer }) => {
    // Add custom webpack configuration if needed
    return config;
  },
  trailingSlash: true,
};