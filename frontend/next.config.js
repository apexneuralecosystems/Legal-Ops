/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    swcMinify: true,
    productionBrowserSourceMaps: false,
    experimental: {
        forceSwcTransforms: true,
    },
    env: {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005',
    },
    webpack: (config, { isServer }) => {
        // Fix for "Unexpected end of JSON input" error
        config.optimization = {
            ...config.optimization,
            moduleIds: 'deterministic',
        };
        return config;
    },
}

module.exports = nextConfig


