from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from celery.result import AsyncResult
from celery_app import celery_app
from services.tasks import run_audit
from schemas.scan import ScanRequest, ScanResponse
from schemas.users import UserResponse
from core.scan_service import scan_service
from utils.dependencies import get_current_user

router = APIRouter()
final_result = ''
api_key = "AIzaSyAZWc99HhZlpcehuCnEHLm_xNQwgIPUzGs"

@router.post("/scan")
async def run_scan(
    scan_request: ScanRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Run a comprehensive scan based on the provided request.
    """
    url = scan_request.url
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    scan_id = await scan_service.create_scan(current_user.id, url)
    if not scan_id:
        raise HTTPException(status_code=500, detail="Failed to create scan")

    run_audit.delay(scan_id=scan_id, url=url, api_key=api_key)

    new_scan = await scan_service.get_scan_by_id(scan_id)
    if not new_scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return new_scan

@router.get("/scan/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    current_user: UserResponse = Depends(get_current_user)
    ):
    """
    Get scan details by ID.
    """
    scan = await scan_service.get_scan_by_id(scan_id)
    if not scan or scan.userId != current_user.id:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@router.get("/scans", response_model=List[ScanResponse])
async def get_scans(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all scans for the current user.
    """
    scans = await scan_service.get_scans_by_user(current_user.id)
    return scans