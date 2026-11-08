/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    tsconfigPath: './tsconfig.json',
  },
  images: {
    unoptimized: true,
  },
  experimental: {
    optimizePackageImports: ["@radix-ui/react-*", "recharts"],
  },
  productionBrowserSourceMaps: false,
  swcMinify: true,
  compress: true,
}

export default nextConfig
