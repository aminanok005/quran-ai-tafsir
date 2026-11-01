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
    serverComponents: true,
    optimizeCss: true,
    optimizePackageImports: ["@headlessui/react", "lucide-react"],
  },
  i18n: {
    locales: ["th", "ar", "en"],
    defaultLocale: "th",
    localesSeparator: ",",
  },
  asyncHeaders: async () => [
    {
      source: "/_next/static/(*.*)",
      headers: [
        {
          key: "Cache-Control",
          value: "public, max-age=31536000, immutable",
        },
      ],
    },
    {
      source: "/api/(.*)",
      headers: [
        {
          key: "Cache-Control",
          value: "public, max-age=60, stale-while-revalidate=300",
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