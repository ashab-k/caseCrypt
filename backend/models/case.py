"""
Pydantic models — Case & Document
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = ""
    case_type: Literal["criminal", "civil", "contract", "other"] = "other"


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    case_type: Optional[Literal["criminal", "civil", "contract", "other"]] = None


class CaseOut(BaseModel):
    id: str
    title: str
    description: str
    case_type: str
    owner_id: str
    document_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentOut(BaseModel):
    id: str
    case_id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    sha256: str
    uploaded_at: datetime
    extracted: bool = False
