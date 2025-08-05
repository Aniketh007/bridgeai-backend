import uuid
import re
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import google.generativeai as genai
from celery.result import AsyncResult
from celery_app import celery_app
from services.tasks import run_audit
from schemas.scan import ScanRequest, ScanResponse

router = APIRouter()
final_result = ''
api_key = "AIzaSyBiQl3KNJpE-_iaH4-QVXPL-Y2YYcHLSNg"

@router.post("/scan")
def run_scan(scan_request: ScanRequest):
    """
    Run a comprehensive scan based on the provided request.
    """
    url = scan_request.url
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    task = run_audit.delay(url=url, api_key=api_key)

    return {"task_id": task.id}

@router.get("/scan/{task_id}/status")
def scan_status(task_id: str):
    """Return current progress or result once finished."""
    result = AsyncResult(task_id, app=celery_app)
    if result.state == "PENDING":
        return {"status": "pending", "progress": 0}
    elif result.state == "PROGRESS":
        meta = result.info
        return {
            "status": "in_progress",
            "current": meta.get("current", 0),
            "total":   meta.get("total", 1),
            "last_completed": meta.get("last_completed")
        }
    elif result.state == "SUCCESS":
        return {"status": "complete", "result": result.get()}
    else:
        return {"status": "failed", "error": str(result.info)}
