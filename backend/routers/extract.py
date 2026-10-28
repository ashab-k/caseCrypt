"""
Extract router — OCR + NLP pipeline, timeline, entities, knowledge graph
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from database import get_db
from middleware.auth import get_current_user
from models.extraction import (
    CaseEntitiesOut,
    ExtractResponse,
    ExtractionOut,
    KnowledgeGraphOut,
    TimelineOut,
)
from models.orm import Case, Document, Extraction, User
from services.nlp_service import extract_structured, run_spacy
from services.ocr_service import extract_text, pages_to_raw_text
from services.timeline_service import (
    aggregate_entities,
    build_knowledge_graph,
    build_timeline,
    serialize_extraction,
)

router = APIRouter()


async def _get_owned_case(db: AsyncSession, case_id: str, owner_id: str) -> Case:
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.owner_id == owner_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


async def _load_extraction_pairs(
    db: AsyncSession, case_id: str, owner_id: str
) -> list[tuple[Extraction, Document]]:
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.extraction))
        .where(Document.case_id == case_id, Document.owner_id == owner_id)
        .order_by(Document.uploaded_at.asc())
    )
    pairs: list[tuple[Extraction, Document]] = []
    for doc in result.scalars().all():
        if doc.extraction is not None:
            pairs.append((doc.extraction, doc))
    return pairs


def _run_pipeline(file_path: Path, file_type: str) -> dict:
    pages = extract_text(file_path, file_type)
    raw_text = pages_to_raw_text(pages)
    ocr_used = any(p.is_ocr for p in pages)
    spacy_entities = run_spacy(raw_text)
    structured = extract_structured(raw_text, spacy_entities)
    return {
        "raw_text": raw_text,
        "ocr_used": ocr_used,
        "structured": structured,
    }


@router.post("/{case_id}/extract", response_model=ExtractResponse)
async def extract_case_documents(
    case_id: str,
    force: bool = Query(False, description="Re-run extraction on already processed docs"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await _get_owned_case(db, case_id, current_user.id)

    result = await db.execute(
        select(Document)
        .options(selectinload(Document.extraction))
        .where(Document.case_id == case_id, Document.owner_id == current_user.id)
        .order_by(Document.uploaded_at.asc())
    )
    documents = list(result.scalars().all())
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents uploaded for this case",
        )

    processed = 0
    skipped = 0
    extractions: list[ExtractionOut] = []
    now = datetime.utcnow()

    for doc in documents:
        if doc.extracted and doc.extraction is not None and not force:
            skipped += 1
            extractions.append(
                ExtractionOut(**serialize_extraction(doc.extraction, doc))
            )
            continue

        file_path = settings.upload_dir / doc.filename
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Physical file missing for document '{doc.original_name}'",
            )

        try:
            payload = await asyncio.to_thread(_run_pipeline, file_path, doc.file_type)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Extraction failed for '{doc.original_name}': {exc}",
            ) from exc

        structured = payload["structured"]
        if doc.extraction is not None:
            extraction = doc.extraction
        else:
            extraction = Extraction(document_id=doc.id, case_id=case_id)
            db.add(extraction)

        extraction.raw_text = payload["raw_text"]
        extraction.parties_json = json.dumps(structured.get("parties") or {})
        extraction.dates_json = json.dumps(structured.get("dates") or [])
        extraction.events_json = json.dumps(structured.get("events") or [])
        extraction.claims_json = json.dumps(structured.get("claims") or [])
        extraction.cited_provisions_json = json.dumps(
            structured.get("cited_provisions") or []
        )
        extraction.spacy_entities_json = json.dumps(
            structured.get("spacy_entities") or []
        )
        extraction.extracted_at = now
        extraction.ocr_used = bool(payload["ocr_used"])
        extraction.extraction_method = str(
            structured.get("extraction_method") or "heuristic"
        )

        doc.extracted = True
        processed += 1
        await db.flush()
        await db.refresh(extraction)
        extractions.append(ExtractionOut(**serialize_extraction(extraction, doc)))

    case.updated_at = now
    return ExtractResponse(
        case_id=case_id,
        processed=processed,
        skipped=skipped,
        extractions=extractions,
    )


@router.get("/{case_id}/timeline", response_model=TimelineOut)
async def get_timeline(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_case(db, case_id, current_user.id)
    pairs = await _load_extraction_pairs(db, case_id, current_user.id)
    built = build_timeline(pairs)
    return TimelineOut(
        case_id=case_id,
        events=built["events"],
        last_updated=built["last_updated"],
    )


@router.get("/{case_id}/entities", response_model=CaseEntitiesOut)
async def get_entities(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_case(db, case_id, current_user.id)
    pairs = await _load_extraction_pairs(db, case_id, current_user.id)
    aggregated = aggregate_entities(pairs)
    return CaseEntitiesOut(case_id=case_id, **aggregated)


@router.get("/{case_id}/knowledge-graph", response_model=KnowledgeGraphOut)
async def get_knowledge_graph(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_case(db, case_id, current_user.id)
    pairs = await _load_extraction_pairs(db, case_id, current_user.id)
    graph = build_knowledge_graph(pairs, case_id)
    return KnowledgeGraphOut(**graph)
