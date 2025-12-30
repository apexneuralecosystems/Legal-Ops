/** @type {import('next').NextConfig} */
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
                destination: 'http://127.0.0.1:8091/api/:path*',
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


