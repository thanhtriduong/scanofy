import shutil
import uuid
import mimetypes
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.document import Document
from app.models.document_job import DocumentJob
from app.models.ocr_output import OCROutput
from app.models.page import Page
from app.models.block import Block
from app.models.span import Span
from app.schemas.document import (
    BlockRead,
    DocumentRead,
    DocumentPreviewBlock,
    DocumentPreviewPage,
    DocumentPreviewResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
    OCROutputRead,
    PageRead,
    SpanRead,
)
from app.services.document_processing import run_document_processing
from app.services.engine_orchestrator import default_orchestrator
from app.services.artifact_storage import artifact_root

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_FILE_TYPES = {"pdf", "docx", "jpg", "jpeg", "png", "webp"}


@router.get("/{document_id}/outputs/{output_id}/artifacts/{artifact_path:path}")
def get_output_artifact(document_id: str, output_id: str, artifact_path: str, db: Session = Depends(get_db)) -> FileResponse:
    output = db.get(OCROutput, output_id)
    if output is None or output.document_id != document_id:
        raise HTTPException(status_code=404, detail="OCR output not found.")
    manifest = (output.raw_output or {}).get("_scanofy", {}).get("artifacts", [])
    if artifact_path not in {entry["path"] for entry in manifest}:
        raise HTTPException(status_code=404, detail="Artifact not in output manifest.")
    try:
        root = (artifact_root(output.raw_output or {}) / document_id).resolve()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Unknown artifact storage.") from exc
    target = (root / artifact_path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(status_code=404, detail="Artifact file not found.")
    media_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    inline = media_type in {"image/png", "image/jpeg", "image/webp", "application/pdf"}
    return FileResponse(target, filename=target.name, media_type=media_type,
                        content_disposition_type="inline" if inline else "attachment",
                        headers={"X-Content-Type-Options": "nosniff"})


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
    stored_name = f"original.{file_type}"
    stored_path = document_dir / stored_name

    try:
        document_dir.mkdir(parents=True, exist_ok=False)
        bytes_written = 0
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        with stored_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
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
    except HTTPException:
        db.rollback()
        shutil.rmtree(document_dir, ignore_errors=True)
        raise
    except Exception as exc:
        db.rollback()
        shutil.rmtree(document_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not persist the uploaded document.",
        ) from exc
    finally:
        await file.close()

    background_tasks.add_task(run_document_processing, document.id, job.id, str(stored_path))
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


@router.get("/{document_id}/file", response_class=FileResponse)
def get_document_file(document_id: str, db: Session = Depends(get_db)) -> FileResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    file_path = Path(document.storage_url)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found.")

    media_type = mimetypes.guess_type(document.filename)[0] or "application/octet-stream"
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=document.filename,
        content_disposition_type="inline",
    )


@router.get("/{document_id}/preview", response_model=DocumentPreviewResponse)
def get_document_preview(
    document_id: str, db: Session = Depends(get_db)
) -> DocumentPreviewResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    latest_output = db.scalars(
        select(OCROutput)
        .where(OCROutput.document_id == document_id)
        .order_by(desc(OCROutput.created_at))
        .limit(1)
    ).first()

    if latest_output is not None:
        normalized = default_orchestrator().normalize(
            {
                "engine": latest_output.engine,
                "raw_output": latest_output.raw_output or {},
                "markdown_output": latest_output.markdown_output,
                "average_confidence": latest_output.average_confidence,
            },
            validate_raw=False,  # Preserve read-only preview of historical Markdown snapshots.
        )
        measured_pages = {page["page_number"]: page for page in (document.profile or {}).get("pages", [])}
        for page in normalized.get("pages", []):
            measured = measured_pages.get(page["page_number"])
            if measured:
                page.update({field: measured.get(field) for field in ("width", "height", "rotation")})
        pages = [DocumentPreviewPage(**page) for page in normalized.get("pages", [])]
        blocks = [
            DocumentPreviewBlock(
                id=f"{latest_output.id}:page-{block['page_number']}-block-{position}",
                parse_run_id=latest_output.id,
                heading_level=block.get("heading_level"),
                spans=block.get("spans", []),
                is_handwritten=block.get("is_handwritten"),
                needs_review=block.get("needs_review", False),
                quality_score=block.get("quality_score"),
                page_number=block["page_number"],
                block_type=block.get("block_type", "unknown"),
                text=block.get("text"),
                bbox=block.get("bbox"),
                reading_order=block.get("reading_order"),
                confidence=block.get("confidence"),
                source_engine=block.get("source_engine"),
                coordinate_system=block.get("coordinate_system"),
            )
            for position, block in enumerate(normalized.get("blocks", []), 1)
        ]
        return DocumentPreviewResponse(
            document=document,
            pages=pages,
            blocks=blocks,
            source_engine=normalized.get("source"),
            parse_run_id=latest_output.id,
        )

    persisted_pages = list(
        db.scalars(select(Page).where(Page.document_id == document_id).order_by(Page.page_number)).all()
    )
    persisted_blocks = list(
        db.scalars(
            select(Block)
            .where(Block.document_id == document_id)
            .order_by(Block.page_number, Block.reading_order)
        ).all()
    )
    return DocumentPreviewResponse(
        document=document,
        pages=[
            DocumentPreviewPage(
                page_number=page.page_number,
                width=page.width,
                height=page.height,
                raw_text=page.raw_text,
                rotation=page.rotation,
                image_url=page.image_url,
            )
            for page in persisted_pages
        ],
        blocks=[
            DocumentPreviewBlock(
                id=block.id,
                page_number=block.page_number,
                block_type=block.block_type,
                is_handwritten=block.is_handwritten,
                needs_review=block.needs_review,
                quality_score=block.quality_score,
                heading_level=block.heading_level,
                text=block.text,
                bbox=block.bbox,
                reading_order=block.reading_order,
                confidence=block.confidence,
                source_engine=block.source_engine,
                coordinate_system=(block.raw_json or {}).get("coordinate_system"),
            )
            for block in persisted_blocks
        ],
        source_engine=persisted_blocks[0].source_engine if persisted_blocks else None,
    )


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


@router.post("/{document_id}/retry", response_model=DocumentStatusResponse)
def retry_document(
    document_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> DocumentStatusResponse:
    document = db.scalars(
        select(Document).where(Document.id == document_id).with_for_update()
    ).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if document.status != "failed":
        raise HTTPException(status_code=409, detail="Only failed analysis can be retried.")
    source = Path(document.storage_url)
    if not source.is_file():
        raise HTTPException(status_code=404, detail="Document file not found.")
    document.status = "uploaded"
    job = DocumentJob(document_id=document.id, status="queued", current_step="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(run_document_processing, document.id, job.id, str(source))
    return DocumentStatusResponse(
        document_id=document.id, status=document.status, profile=document.profile,
        router_decision=document.router_decision, latest_job=job,
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
    document = db.scalars(select(Document).where(Document.id == document_id).with_for_update()).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if document.status in {"uploaded", "queued", "processing", "normalizing"}:
        raise HTTPException(status_code=409, detail="Tài liệu đang xử lý. Vui lòng đợi trước khi xóa.")

    settings = get_settings()
    targets = []
    for root in {settings.upload_root, settings.mineru_output_root, settings.ocr_output_root}:
        target = root / document.id
        if target.is_symlink() or target.resolve().parent != root.resolve():
            raise HTTPException(status_code=400, detail="Invalid document storage path.")
        targets.append(target)
    try:
        for target in targets:
            if target.exists():
                shutil.rmtree(target)
    except OSError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Không thể dọn file tài liệu. Vui lòng thử lại.") from exc
    db.delete(document)
    db.commit()


@router.get("/{document_id}/spans", response_model=list[SpanRead])
def get_spans(
    document_id: str, page_number: int | None = None,
    block_id: str | None = None, db: Session = Depends(get_db),
) -> list[Span]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    query = select(Span).join(Block, Span.block_id == Block.id).where(Span.document_id == document_id)
    if page_number is not None:
        query = query.where(Span.page_number == page_number)
    if block_id is not None:
        query = query.where(Span.block_id == block_id)
    return list(db.scalars(query.order_by(Span.page_number, Block.reading_order, Span.reading_order)).all())
