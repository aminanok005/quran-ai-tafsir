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
  webpack: (config, { isServer }) => {
    // Add custom webpack configuration if needed
    return config;
  },
  trailingSlash: true,
};