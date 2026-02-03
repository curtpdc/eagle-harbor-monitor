/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://eagle-harbor.centralus.azurecontainer.io:8000',
  },
}

module.exports = nextConfig
