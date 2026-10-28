"""Public-statute research contracts. No case material enters this API."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Act = Literal['IPC', 'CrPC', 'Constitution', 'Evidence Act', 'IT Act']


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    act: Act | None = None
    top_k: int = Field(default=5, ge=1, le=10)

    @field_validator('question')
    @classmethod
    def clean_question(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError('Enter a question of at least 3 characters')
        return value


class ResearchSource(BaseModel):
    id: str
    act: str
    section: str
    title: str
    text: str
    url: str
    page: int
    score: float
    historical: bool = False


class SearchResponse(BaseModel):
    sources: list[ResearchSource]
    retrieval_mode: str


class ResearchResponse(SearchResponse):
    answer: str
    confidence: Literal['high', 'medium', 'low']
    retrieved_chunks: int
    generation_mode: Literal['openai', 'extractive', 'unavailable']
    notice: str


class ActStatus(BaseModel):
    act: str
    chunks: int
    sections: int
    historical: bool
    source_url: str


class CorpusStatus(BaseModel):
    seeded: bool
    complete: bool
    total_chunks: int
    acts: list[ActStatus]
    seeded_at: str | None = None
    embedding_model: str
    generation_available: bool
    notice: str
