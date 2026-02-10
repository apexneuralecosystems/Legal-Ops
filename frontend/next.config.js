/** @type {import('next').NextConfig} */

const nextConfig = {
    output: 'standalone', // Enable for Docker deployment
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
        // Evaluate BACKEND_URL at runtime (not build time)
        // Ensure it points to the 'backend' service in Docker network
        const BACKEND_URL = process.env.BACKEND_URL ||
            process.env.INTERNAL_API_URL ||
            'http://backend:8091';

        console.log(`[Next.js Runtime] Proxying /api to: ${BACKEND_URL}`);

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


