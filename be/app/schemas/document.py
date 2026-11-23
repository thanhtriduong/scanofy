from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentJobRead(BaseModel):
    id: str
    document_id: str
    job_type: str
    status: str
    current_step: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: str
    user_id: str | None
    filename: str
    file_type: str
    storage_url: str
    status: str
    profile: dict | None
    router_decision: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    document: DocumentRead
    job: DocumentJobRead


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str
    profile: dict | None
    router_decision: dict | None
    latest_job: DocumentJobRead | None


class OCROutputRead(BaseModel):
    id: str
    document_id: str
    engine: str
    raw_output: dict | None
    markdown_output: str | None
    average_confidence: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PageRead(BaseModel):
    id: str
    document_id: str
    page_number: int
    width: float | None
    height: float | None
    image_url: str | None
    raw_text: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlockRead(BaseModel):
    id: str
    document_id: str
    page_id: str | None
    page_number: int
    block_type: str
    text: str | None
    corrected_text: str | None
    bbox: list | None
    reading_order: int | None
    confidence: float | None
    correction_confidence: float | None
    needs_review: bool
    source_engine: str | None
    raw_json: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentPreviewPage(BaseModel):
    page_number: int
    width: float | None
    height: float | None
    raw_text: str | None


class DocumentPreviewBlock(BaseModel):
    id: str
    page_number: int
    block_type: str
    text: str | None
    bbox: list | None
    reading_order: int | None
    confidence: float | None
    source_engine: str | None
    coordinate_system: str | None


class DocumentPreviewResponse(BaseModel):
    document: DocumentRead
    pages: list[DocumentPreviewPage]
    blocks: list[DocumentPreviewBlock]
    source_engine: str | None
