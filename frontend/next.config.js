/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use 'export' only for production static builds (Azure Static Web Apps)
  // For local development, we need the dev server without static export
  output: process.env.NODE_ENV === 'production' ? 'export' : undefined,
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  },
}

module.exports = nextConfig
