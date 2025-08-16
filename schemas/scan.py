from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class ScanResponse(BaseModel):
    url: str = Field(..., description="URL that was scanned")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of when the scan was performed")
    result: Optional[dict] = Field(None, description="Results of the scan categorized by type")
    duration: Optional[float] = Field(None, description="Duration of the scan in seconds")

    class Config:
        orm_mode = True 

class ScanRequest(BaseModel):
    url: str = Field(..., description="URL to scan")