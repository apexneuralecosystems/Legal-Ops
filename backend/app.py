from main import app
from core.config import settings

# Compatibility shim for deployments that default to looking for 'app:app'
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.BACKEND_PORT)

