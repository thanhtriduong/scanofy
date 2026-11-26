import json
from pathlib import Path

from sqlalchemy import select
from app.commands.renormalize import renormalize
from app.models.document import Document
from app.models.ocr_output import OCROutput
from app.models.span import Span


def test_dry_run_then_apply_saved_output_without_model(db_session):
    source = json.loads((Path(__file__).parent / "fixtures/mineru_contract.json").read_text(encoding="utf-8"))
    document = Document(filename="sample.pdf", file_type="pdf", storage_url="not-needed", status="parsed")
    db_session.add(document)
    db_session.flush()
    output = OCROutput(document_id=document.id, engine="mineru", raw_output=source["raw_output"])
    db_session.add(output)
    db_session.commit()
    summary = renormalize(db_session, document.id)
    assert summary["spans"] == 3
    assert not summary["applied"]
    assert db_session.scalars(select(Span)).all() == []
    renormalize(db_session, document.id, apply=True)
    first_ids = {span.id for span in db_session.scalars(select(Span)).all()}
    renormalize(db_session, document.id, apply=True)
    assert {span.id for span in db_session.scalars(select(Span)).all()} == first_ids
    assert len(first_ids) == 3
