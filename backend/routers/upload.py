"""
Upload router — case document uploads, listing, deletion, and file retrieval
"""
import hashlib
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from middleware.auth import get_current_user
from models.case import DocumentOut
from models.orm import Case, Document, User

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}


def _serialize_document(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        case_id=doc.case_id,
        filename=doc.filename,
        original_name=doc.original_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        sha256=doc.sha256,
        uploaded_at=doc.uploaded_at,
        extracted=doc.extracted,
    )


async def _get_owned_case(
    db: AsyncSession, case_id: str, owner_id: str
) -> Case:
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.owner_id == owner_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


@router.post(
    "/{case_id}/upload",
    response_model=list[DocumentOut],
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents(
    case_id: str,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await _get_owned_case(db, case_id, current_user.id)

    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")

    saved_documents: list[Document] = []
    now = datetime.utcnow()

    for upload in files:
        original_filename = upload.filename or "unnamed_file"
        file_ext = Path(original_filename).suffix.lower()

        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported file format '{file_ext}'. "
                    f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                ),
            )

        unique_prefix = uuid.uuid4().hex[:12]
        safe_filename = f"{unique_prefix}_{Path(original_filename).name}"
        destination_path = settings.upload_dir / safe_filename

        hasher = hashlib.sha256()
        bytes_written = 0

        with open(destination_path, "wb") as f:
            while chunk := await upload.read(65536):
                hasher.update(chunk)
                f.write(chunk)
                bytes_written += len(chunk)

        doc = Document(
            case_id=case_id,
            owner_id=current_user.id,
            filename=safe_filename,
            original_name=original_filename,
            file_type=file_ext.lstrip("."),
            file_size=bytes_written,
            sha256=hasher.hexdigest(),
            uploaded_at=now,
            extracted=False,
        )
        db.add(doc)
        saved_documents.append(doc)

    case.document_count += len(saved_documents)
    case.updated_at = now
    await db.flush()
    for doc in saved_documents:
        await db.refresh(doc)

    return [_serialize_document(d) for d in saved_documents]


@router.get("/{case_id}/documents", response_model=list[DocumentOut])
async def list_documents(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_case(db, case_id, current_user.id)

    result = await db.execute(
        select(Document)
        .where(Document.case_id == case_id, Document.owner_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
    )
    return [_serialize_document(d) for d in result.scalars().all()]


@router.delete("/{case_id}/documents/{doc_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    case_id: str,
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await _get_owned_case(db, case_id, current_user.id)

    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.case_id == case_id,
            Document.owner_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    file_path = settings.upload_dir / doc.filename
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass

    await db.delete(doc)
    if case.document_count > 0:
        case.document_count -= 1
    case.updated_at = datetime.utcnow()

    return {"status": "deleted", "doc_id": doc_id}


@router.get("/{case_id}/documents/{doc_id}/download")
async def download_document(
    case_id: str,
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_case(db, case_id, current_user.id)

    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.case_id == case_id,
            Document.owner_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    file_path = settings.upload_dir / doc.filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file missing on server",
        )

    media_type = "application/pdf" if doc.file_type == "pdf" else "application/octet-stream"
    return FileResponse(
        path=file_path,
        filename=doc.original_name,
        media_type=media_type,
    )
