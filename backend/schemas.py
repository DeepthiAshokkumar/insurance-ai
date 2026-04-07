from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional, List

class ClaimResult(BaseModel):
    status: str
    extracted_details: Optional[Dict[str, Any]] = None
    missing_fields: Optional[List[str]] = []

class ClaimResponse(BaseModel):
    id: int
    filename: str
    status: str
    extracted_details: Optional[Dict[str, Any]] = None
    missing_fields: Optional[List[str]] = []
    timestamp: datetime

    class Config:
        from_attributes = True
