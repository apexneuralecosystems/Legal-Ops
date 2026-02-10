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
        // Log environment keys to help debug Dokploy networking
        const envKeys = Object.keys(process.env).filter(k => k.includes('URL') || k.includes('API') || k.includes('BACKEND'));
        console.log(`[Next.js Runtime] Available URL Env Vars: ${envKeys.join(', ')}`);

        // Evaluate BACKEND_URL at runtime (not build time)
        // 1. Try explicit BACKEND_URL
        // 2. Try INTERNAL_API_URL
        // 3. Try PUBLIC_API_URL (last resort, slower but works)
        // 4. Hard fallback to Docker default
        const BACKEND_URL = process.env.BACKEND_URL ||
            process.env.INTERNAL_API_URL ||
            process.env.NEXT_PUBLIC_API_URL ||
            'http://backend:8091';

        console.log(`[Next.js Runtime] STARTING PROXY: /api -> ${BACKEND_URL}`);

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


