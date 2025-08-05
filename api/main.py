from fastapi import APIRouter
from api.v1.routes import scan

api_router = APIRouter()
api_router.include_router(scan.router, tags=["scan"])