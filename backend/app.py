from main import app

# Compatibility shim for deployments that default to looking for 'app:app'
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)
