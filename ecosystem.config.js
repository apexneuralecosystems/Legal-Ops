const os = require('os');
const isWindows = os.platform() === 'win32';

module.exports = {
    apps: [
        {
            name: "legal-ops-backend",
            cwd: "backend",
            script: "main.py",
            interpreter: isWindows ? "venv/Scripts/python" : "venv/bin/python",
            interpreter_args: "", // Optional: add python args here if needed
            env: {
                NODE_ENV: "production",
                LLM_PROVIDER: "openrouter",
            },
        },
        {
            name: "legal-ops-frontend",
            cwd: "frontend",
            script: "npm",
            args: "start -- -p 8006",
            interpreter: "none",
            env: {
                NODE_ENV: "production",
            },
        },
    ],
};
