"""
Cases router — CRUD operations for legal cases
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from middleware.auth import get_current_user
from models.case import CaseCreate, CaseOut, CaseUpdate
from models.orm import Case, Document, User

router = APIRouter()


def _serialize_case(case: Case) -> CaseOut:
    return CaseOut(
        id=case.id,
        title=case.title,
        description=case.description or "",
        case_type=case.case_type,
        owner_id=case.owner_id,
        document_count=case.document_count,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    case = Case(
        title=payload.title.strip(),
        description=(payload.description or "").strip(),
        case_type=payload.case_type,
        owner_id=current_user.id,
        document_count=0,
        created_at=now,
        updated_at=now,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return _serialize_case(case)


@router.get("", response_model=list[CaseOut])
async def list_cases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Case)
        .where(Case.owner_id == current_user.id)
        .order_by(Case.created_at.desc())
    )
    return [_serialize_case(c) for c in result.scalars().all()]


@router.get("/{case_id}", response_model=CaseOut)
async def get_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.owner_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return _serialize_case(case)


@router.put("/{case_id}", response_model=CaseOut)
async def update_case(
    case_id: str,
    payload: CaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.owner_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update",
        )

    for key, value in update_data.items():
        setattr(case, key, value)
    case.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(case)
    return _serialize_case(case)


@router.delete("/{case_id}", status_code=status.HTTP_200_OK)
async def delete_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.owner_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    docs_result = await db.execute(
        select(Document).where(Document.case_id == case_id, Document.owner_id == current_user.id)
    )
    for doc in docs_result.scalars().all():
        file_path = settings.upload_dir / doc.filename
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass
        await db.delete(doc)

    await db.delete(case)
    return {"status": "deleted", "case_id": case_id}
