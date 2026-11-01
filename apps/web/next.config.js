module.exports = {
  reactStrictMode: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  eslint: {
    dirs: ["app"],
  },
  images: {
    domains: [
      "localhost",
      "api.quran.foundation",
      "cdn.quran.foundation"
    ],
  },
  i18n: {
    locales: ["th", "ar", "en"],
    defaultLocale: "th",
  },
  async headers() {
    return [
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
        source: "/api/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=60, stale-while-revalidate=300",
          },
        ],
      },
    ];
  },
  trailingSlash: true,
};