/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // Allow proxy and local access for dev
  allowedDevOrigins: ['127.0.0.1', 'localhost', '*.vercel.app'],
  // Turbopack configuration (Next.js 16 default)
  turbopack: {
    // Disable HMR for stability during testing
    moduleIdStrategy: 'named',
  },
}

export default nextConfig
