import asyncio
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_job import DocumentJob
from app.models.ocr_output import OCROutput
from app.models.page import Page
from app.models.block import Block
from app.services.file_profiler import FileProfiler
from app.services.normalizer import Normalizer
from app.services.ocr_engines.mineru_adapter import MinerUAdapter
from app.services.router import DocumentRouter


class DocumentProcessingService:
    def __init__(self, db: Session):
        self.db = db
        self.profiler = FileProfiler()
        self.router = DocumentRouter()
        self.normalizer = Normalizer()
        self.mineru = MinerUAdapter()

    def run_placeholder_pipeline(self, document_id: str, job_id: str, file_path: Path) -> None:
        job = self.db.get(DocumentJob, job_id)
        document = self.db.get(Document, document_id)
        if job is None or document is None:
            return

        try:
            now = datetime.now(timezone.utc)
            job.status = "running"
            job.current_step = "profiling"
            job.started_at = now
            document.status = "processing"
            self.db.commit()

            profile = self.profiler.profile(file_path, document.file_type)
            document.profile = profile
            job.current_step = "routing"
            self.db.commit()

            document.router_decision = self.router.choose_engine(profile)
            self.db.commit()

            engine = document.router_decision.get("engine")
            if engine == "mineru":
                job.current_step = "mineru_parsing"
                self.db.commit()
                ocr_result = self._run_async(self.mineru.parse(file_path))

                ocr_output = OCROutput(
                    document_id=document.id,
                    engine="mineru",
                    raw_output=ocr_result.get("raw_output") or ocr_result,
                    markdown_output=ocr_result.get("markdown_output"),
                    average_confidence=ocr_result.get("average_confidence"),
                )
                self.db.add(ocr_output)
                self.db.flush()

                job.current_step = "normalizing"
                document.status = "normalizing"
                self.db.commit()

                normalized = self.normalizer.normalize(ocr_result)
                self._persist_normalized_output(document.id, normalized)
                document.status = "parsed"
                job.current_step = "parsed"
            else:
                job.current_step = "awaiting_ocr"
                document.status = "awaiting_ocr"

            job.status = "completed"
            job.finished_at = datetime.now(timezone.utc)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            job = self.db.get(DocumentJob, job_id)
            document = self.db.get(Document, document_id)
            if job is not None:
                job.status = "failed"
                job.error_message = str(exc).strip() or type(exc).__name__
                job.finished_at = datetime.now(timezone.utc)
            if document is not None:
                document.status = "failed"
            self.db.commit()

    def _persist_normalized_output(self, document_id: str, normalized: dict) -> None:
        for page_data in normalized.get("pages", []):
            page = Page(
                document_id=document_id,
                page_number=page_data["page_number"],
                width=page_data.get("width"),
                height=page_data.get("height"),
                image_url=page_data.get("image_url"),
                raw_text=page_data.get("raw_text"),
            )
            self.db.add(page)
            self.db.flush()

            for block_data in normalized.get("blocks", []):
                if block_data.get("page_number") != page.page_number:
                    continue
                self.db.add(
                    Block(
                        document_id=document_id,
                        page_id=page.id,
                        page_number=block_data["page_number"],
                        block_type=block_data.get("block_type", "unknown"),
                        text=block_data.get("text"),
                        corrected_text=block_data.get("corrected_text"),
                        bbox=block_data.get("bbox"),
                        reading_order=block_data.get("reading_order"),
                        confidence=block_data.get("confidence"),
                        source_engine=block_data.get("source_engine"),
                        raw_json=block_data.get("raw_json"),
                    )
                )
        self.db.commit()

    def _run_async(self, coroutine):
        return asyncio.run(coroutine)


def run_placeholder_processing(document_id: str, job_id: str, file_path: str) -> None:
    db = SessionLocal()
    try:
        DocumentProcessingService(db).run_placeholder_pipeline(document_id, job_id, Path(file_path))
    finally:
        db.close()
