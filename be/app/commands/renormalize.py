"""Preview/apply normalization from saved raw engine output without model calls."""
import argparse
import json

from pathlib import Path
from sqlalchemy import select, desc

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.ocr_output import OCROutput
from app.services.document_processing import DocumentProcessingService
from app.services.engine_orchestrator import default_orchestrator
from app.services.file_profiler import FileProfiler


def renormalize(db, document_id: str, apply: bool = False, reprofile: bool = False) -> dict:
    document = db.scalars(select(Document).where(Document.id == document_id).with_for_update()).first()
    if document is None:
        raise ValueError("Document not found.")
    if document.status in {"uploaded", "queued", "processing", "normalizing"}:
        raise ValueError("Document is busy; wait for the current job.")
    output = db.scalars(select(OCROutput).where(OCROutput.document_id == document_id).order_by(desc(OCROutput.created_at), desc(OCROutput.id))).first()
    if output is None:
        raise ValueError("No saved engine output. Run parsing first.")
    normalized = default_orchestrator().normalize({"engine": output.engine, "raw_output": output.raw_output, "markdown_output": output.markdown_output})
    profile = FileProfiler().profile(Path(document.storage_url), document.file_type) if reprofile else document.profile
    if profile and profile.get("page_count") is not None and len(normalized["pages"]) != profile["page_count"]:
        raise ValueError("Page count mismatch; no data was changed.")
    for page in normalized["pages"]:
        measured = next((p for p in (profile or {}).get("pages", []) if p["page_number"] == page["page_number"]), None)
        if measured:
            page.update({key: measured.get(key) for key in ("width", "height", "rotation")})
    summary = {"document_id": document_id, "parse_run_id": output.id, "pages": len(normalized["pages"]), "blocks": len(normalized["blocks"]), "spans": sum(len(b["spans"]) for b in normalized["blocks"]), "applied": apply}
    if apply:
        DocumentProcessingService(db)._persist_normalized_output(document.id, normalized, output.id)
        if reprofile:
            document.profile = profile
        document.status = "parsed"
        db.commit()
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--apply", action="store_true", help="Write changes; otherwise dry-run only")
    parser.add_argument("--reprofile", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        try:
            print(json.dumps(renormalize(db, args.document_id, args.apply, args.reprofile)))
        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    main()
