/** @type {import('next').NextConfig} */

// Get backend URL from environment variable, fallback to localhost for local dev
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8091';

const nextConfig = {
    reactStrictMode: true,
    swcMinify: true,
    productionBrowserSourceMaps: false,
    experimental: {
        forceSwcTransforms: true,
        // Increase proxy timeout for long-running AI workflows
        proxyTimeout: 300000, // 5 minutes
    },
    webpack: (config, { isServer }) => {
        // Fix for "Unexpected end of JSON input" error
        config.optimization = {
            ...config.optimization,
            moduleIds: 'deterministic',
        };
        return config;
    },
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: `${BACKEND_URL}/api/:path*`,
            },
        ]
    },
    async headers() {
        return [
            {
                source: '/api/:path*',
                headers: [
                    {
                        key: 'Connection',
                        value: 'keep-alive',
                    },
                    {
                        key: 'Keep-Alive',
                        value: 'timeout=300',
                    },
                ],
            },
        ]
    },
}

module.exports = nextConfig


