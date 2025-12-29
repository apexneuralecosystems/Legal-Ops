module.exports = {
  apps: [
    {
      name: "legalops-api",
      script: "./venv/bin/gunicorn",
      cwd: "./backend",
      args: "main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8091 --timeout 900 --log-level info",
      interpreter: "none",
      autorestart: true,
      max_memory_restart: "1G",
      env: {
        PYTHONPATH: "."
      }
    }
  ]
};
