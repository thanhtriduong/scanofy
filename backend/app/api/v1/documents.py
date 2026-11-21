import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.document import Document
from app.models.document_job import DocumentJob
from app.models.ocr_output import OCROutput
from app.models.page import Page
from app.models.block import Block
from app.schemas.document import (
    BlockRead,
    DocumentRead,
    DocumentStatusResponse,
    DocumentUploadResponse,
    OCROutputRead,
    PageRead,
)
from app.services.document_processing import run_placeholder_processing

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_FILE_TYPES = {"pdf", "docx", "jpg", "jpeg", "png", "webp"}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    settings = get_settings()
    original_name = file.filename or "upload"
    file_type = Path(original_name).suffix.lower().lstrip(".")
    if file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file_type}'. Allowed: {sorted(ALLOWED_FILE_TYPES)}",
        )

    upload_id = str(uuid.uuid4())
    document_dir = settings.upload_root / upload_id
    document_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"original.{file_type}"
    stored_path = document_dir / stored_name

    bytes_written = 0
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    with stored_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            bytes_written += len(chunk)
            if bytes_written > max_bytes:
                buffer.close()
                stored_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Upload exceeds {settings.max_upload_size_mb} MB.",
                )
            buffer.write(chunk)

    document = Document(
        id=upload_id,
        user_id=user_id,
        filename=original_name,
        file_type=file_type,
        storage_url=str(stored_path),
        status="uploaded",
    )
    db.add(document)
    db.flush()

    job = DocumentJob(
        document_id=document.id,
        job_type="process_document",
        status="queued",
        current_step="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(document)
    db.refresh(job)

    background_tasks.add_task(run_placeholder_processing, document.id, job.id, str(stored_path))
    return DocumentUploadResponse(document=document, job=job)


@router.get("", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_db)) -> list[Document]:
    return list(db.scalars(select(Document).order_by(desc(Document.created_at))).all())


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: str, db: Session = Depends(get_db)) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return document


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(document_id: str, db: Session = Depends(get_db)) -> DocumentStatusResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    latest_job = db.scalars(
        select(DocumentJob)
        .where(DocumentJob.document_id == document_id)
        .order_by(desc(DocumentJob.created_at))
        .limit(1)
    ).first()
    return DocumentStatusResponse(
        document_id=document.id,
        status=document.status,
        profile=document.profile,
        router_decision=document.router_decision,
        latest_job=latest_job,
    )


@router.get("/{document_id}/ocr-output", response_model=list[OCROutputRead])
def get_ocr_outputs(document_id: str, db: Session = Depends(get_db)) -> list[OCROutput]:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return list(
        db.scalars(
            select(OCROutput)
            .where(OCROutput.document_id == document_id)
            .order_by(desc(OCROutput.created_at))
        ).all()
    )


@router.get("/{document_id}/pages", response_model=list[PageRead])
def get_pages(document_id: str, db: Session = Depends(get_db)) -> list[Page]:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return list(
        db.scalars(
            select(Page)
            .where(Page.document_id == document_id)
            .order_by(Page.page_number)
        ).all()
    )


@router.get("/{document_id}/blocks", response_model=list[BlockRead])
def get_blocks(document_id: str, db: Session = Depends(get_db)) -> list[Block]:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return list(
        db.scalars(
            select(Block)
            .where(Block.document_id == document_id)
            .order_by(Block.page_number, Block.reading_order)
        ).all()
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, db: Session = Depends(get_db)) -> None:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    storage_path = Path(document.storage_url)
    db.delete(document)
    db.commit()
    if storage_path.exists():
        shutil.rmtree(storage_path.parent, ignore_errors=True)
