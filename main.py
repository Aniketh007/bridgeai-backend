import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ARI Backend API",
    description="API for the ARI Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

from api.v1.routes import scan

app.include_router(scan.router, prefix="/api/v1", tags=["scan"])

@app.get("/")
def read_root():
    """Root endpoint returning API information."""
    return {
        "message": "ARI Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.get("/health")
def health_check():
    """Global health check endpoint."""
    return {"status": "healthy", "service": "ARI Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)