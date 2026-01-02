// PM2 Ecosystem Configuration for Legal-Ops Backend
// Port can be configured via BACKEND_PORT environment variable (default: 8091)

const BACKEND_PORT = process.env.BACKEND_PORT || 8091;

module.exports = {
    apps: [
        {
            name: "legalops-api",
            script: "./venv/bin/gunicorn",
            cwd: "/home/apexneural-legalops-api/htdocs/Legal-Ops/backend",
            args: `main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${BACKEND_PORT} --timeout 900 --log-level info`,
            interpreter: "none",
            autorestart: true,
            max_memory_restart: "1G",
            env: {
                PYTHONPATH: "/home/apexneural-legalops-api/htdocs/Legal-Ops/backend",
                LLM_PROVIDER: "openrouter",
                BACKEND_PORT: BACKEND_PORT
            }
        }
    ]
};

