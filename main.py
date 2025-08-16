import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.init_db import get_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    await get_db.connect()
    print("Database connected")
    yield
    # Code to run on shutdown
    await get_db.disconnect()
    print("Database disconnected")

app = FastAPI(
    title="ARI Backend API",
    description="API for the ARI Backend",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

from api.v1.routes import scan, users

app.include_router(scan.router, prefix="/api/v1", tags=["scan"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])

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