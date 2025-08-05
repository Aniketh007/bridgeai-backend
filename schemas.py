"""
Pydantic schemas for ARI Platform API
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from enum import Enum


class ScanStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WebsiteCategory(str, Enum):
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    BLOG = "blog"
    CORPORATE = "corporate"
    PORTFOLIO = "portfolio"
    NEWS = "news"
    EDUCATIONAL = "educational"
    OTHER = "other"


class ScanResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    url: str


class SubPillarScore(BaseModel):
    id: str
    name: str
    score: float = Field(..., ge=0, le=100)
    max_score: float = 100
    passed: bool
    recommendations: List[str] = []
    details: Dict[str, Any] = {}


class PillarScore(BaseModel):
    id: str
    name: str
    weight: float
    score: float = Field(..., ge=0, le=100)
    max_score: float = 100
    sub_pillars: List[SubPillarScore]


class ScanResult(BaseModel):
    scan_id: str
    url: str
    status: ScanStatus
    website_category: Optional[WebsiteCategory] = None
    overall_score: float = Field(..., ge=0, le=100)
    grade: str  # A+, A, B+, B, C+, C, D, F
    pillar_scores: List[PillarScore]
    recommendations: List[str] = []
    scan_date: datetime
    completion_date: Optional[datetime] = None
    error_message: Optional[str] = None


class ScanHistory(BaseModel):
    scan_id: str
    url: str
    overall_score: float
    grade: str
    website_category: Optional[WebsiteCategory] = None
    scan_date: datetime
    status: ScanStatus


class ScanHistoryResponse(BaseModel):
    scans: List[ScanHistory]
    total: int
    page: int
    page_size: int


# Contact & Support Schemas
class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    company: Optional[str] = None


class DemoRequest(BaseModel):
    name: str
    email: EmailStr
    company: str
    phone: Optional[str] = None
    message: Optional[str] = None


# Report Generation
class ReportRequest(BaseModel):
    scan_id: str
    format: str = "pdf"  # pdf, json, csv


# Error Responses
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Success Response
class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
