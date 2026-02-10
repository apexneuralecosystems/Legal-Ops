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
        const BACKEND_URL = process.env.BACKEND_URL ||
            process.env.INTERNAL_API_URL ||
            process.env.NEXT_PUBLIC_API_URL ||
            'http://backend:8091';

        if (process.env.NODE_ENV !== 'production') {
            const envKeys = Object.keys(process.env).filter(k => k.includes('URL') || k.includes('API') || k.includes('BACKEND'));
            console.log(`[Next.js Runtime] URL Env Vars: ${envKeys.join(', ')}`);
            console.log(`[Next.js Runtime] PROXY: /api -> ${BACKEND_URL}`);
        }

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
                // Security headers for all routes
                source: '/:path*',
                headers: [
                    {
                        key: 'X-Content-Type-Options',
                        value: 'nosniff',
                    },
                    {
                        key: 'X-Frame-Options',
                        value: 'SAMEORIGIN',
                    },
                    {
                        key: 'X-XSS-Protection',
                        value: '1; mode=block',
                    },
                    {
                        key: 'Referrer-Policy',
                        value: 'strict-origin-when-cross-origin',
                    },
                    {
                        key: 'Permissions-Policy',
                        value: 'camera=(), microphone=(), geolocation=()',
                    },
                    {
                        key: 'Strict-Transport-Security',
                        value: 'max-age=31536000; includeSubDomains',
                    },
                ],
            },
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


