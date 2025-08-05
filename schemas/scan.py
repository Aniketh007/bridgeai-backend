from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class ScanResponse(BaseModel):
    scan_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the scan")
    url: str = Field(..., description="URL that was scanned")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of when the scan was performed")
    results: Dict[str, Any] = Field(..., description="Results of the scan categorized by type")
    duration: Optional[float] = Field(None, description="Duration of the scan in seconds")

    class Config:
        schema_extra = {
            "example": {
                "scan_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2023-10-01T12:00:00Z",
                "results": {
                    "agent_identification": {"score": 0.95, "details": "..."},
                    "conversational_bot": {"score": 0.85, "details": "..."},
                    "error_recovery": {"score": 0.75, "details": "..."}
                },
                "recommendations": [
                    "Improve agent identification accuracy",
                    "Enhance conversational bot capabilities",
                    "Strengthen error recovery mechanisms"
                ]
            }
        }

class ScanRequest(BaseModel):
    url: str = Field(..., description="URL to scan")