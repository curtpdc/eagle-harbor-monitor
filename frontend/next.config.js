/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://eagle-harbor.centralus.azurecontainer.io:8000',
  },
}

module.exports = nextConfig
