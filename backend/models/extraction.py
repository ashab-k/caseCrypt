"""
Pydantic schemas — Phase 2 extraction, timeline, entities
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Parties(BaseModel):
    petitioner: list[str] = Field(default_factory=list)
    respondent: list[str] = Field(default_factory=list)
    counsel: list[str] = Field(default_factory=list)


class DateMention(BaseModel):
    date: str
    event: str = ""


class ExtractedEvent(BaseModel):
    date: Optional[str] = None
    description: str
    type: Literal["filing", "hearing", "judgment", "incident", "other"] = "other"
    page_number: Optional[int] = None


class CitedProvision(BaseModel):
    act: str
    section: str
    description: str = ""


class SpacyEntity(BaseModel):
    label: str
    text: str


class ExtractionOut(BaseModel):
    id: str
    document_id: str
    case_id: str
    source_document: str
    parties: Parties
    dates: list[DateMention]
    events: list[ExtractedEvent]
    claims: list[str]
    cited_provisions: list[CitedProvision]
    spacy_entities: list[SpacyEntity] = Field(default_factory=list)
    extracted_at: datetime
    ocr_used: bool
    extraction_method: str
    text_preview: str = ""


class ExtractResponse(BaseModel):
    case_id: str
    processed: int
    skipped: int
    extractions: list[ExtractionOut]


class TimelineEventOut(BaseModel):
    date: Optional[str] = None
    description: str
    type: str
    source_document: str
    document_id: str
    document_type: str
    page_number: Optional[int] = None


class TimelineOut(BaseModel):
    case_id: str
    events: list[TimelineEventOut]
    last_updated: Optional[datetime] = None


class CaseEntitiesOut(BaseModel):
    case_id: str
    parties: Parties
    dates: list[DateMention]
    claims: list[str]
    cited_provisions: list[CitedProvision]
    spacy_entities: list[SpacyEntity] = Field(default_factory=list)
    document_count_extracted: int = 0


class GraphNode(BaseModel):
    id: str
    label: str
    group: str


class GraphLink(BaseModel):
    source: str
    target: str
    label: str = ""


class KnowledgeGraphOut(BaseModel):
    case_id: str
    nodes: list[GraphNode]
    links: list[GraphLink]
