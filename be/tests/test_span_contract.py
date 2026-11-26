import json
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.span import Span
from app.services.normalizer import Normalizer
from app.services.document_processing import DocumentProcessingService


def fixture_output():
    return json.loads((Path(__file__).parent / "fixtures/mineru_contract.json").read_text(encoding="utf-8"))


def test_span_geometry_is_not_inherited_from_block():
    result = Normalizer().normalize(fixture_output())
    title, paragraph = result["blocks"]
    assert title["bbox"] is not None
    assert title["spans"][0]["bbox"] is None
    assert title["spans"][0]["coordinate_system"] is None
    assert paragraph["spans"][0]["text"] == "Công thức: "
    assert paragraph["spans"][1]["span_type"] == "inline_equation"
    assert paragraph["spans"][1]["coordinate_system"] == "normalized_0_1"


def test_shared_normalized_fixture_and_schema():
    from app.schemas.normalized import NormalizedDocument
    root = Path(__file__).resolve().parents[2] / "shared/contracts"
    fixture = json.loads((root / "normalized-document.fixture.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "normalized-document.schema.json").read_text(encoding="utf-8"))
    assert NormalizedDocument.model_validate(fixture).model_dump() == Normalizer().normalize(fixture_output())
    assert schema == NormalizedDocument.model_json_schema()
    title = fixture["blocks"][0]
    assert title["block_type"] == "heading"
    assert title["is_handwritten"] is None
    assert title["quality_score"] is None


@pytest.mark.parametrize("engine,source,expected", [("mineru", "paragraph_title", "heading"), ("paddleocr", "formula", "equation"), ("chandra", "section_header", "heading"), ("vintern", "text", "paragraph"), ("mineru", "unrecognized", "unknown")])
def test_block_type_mapping(engine, source, expected):
    from app.services.block_types import canonical_block_type
    assert canonical_block_type(engine, source) == expected


def test_normalized_contract_rejects_invalid_quality_and_page_reference():
    from app.schemas.normalized import NormalizedDocument
    from pydantic import ValidationError
    fixture = Normalizer().normalize(fixture_output())
    fixture["blocks"][0]["quality_score"] = 1.2
    with pytest.raises(ValidationError):
        NormalizedDocument.model_validate(fixture)
    fixture["blocks"][0]["quality_score"] = None
    fixture["blocks"][0]["page_number"] = 99
    with pytest.raises(ValidationError):
        NormalizedDocument.model_validate(fixture)


@pytest.mark.anyio
async def test_spans_api_repeat_normalization_and_delete(client, db_session):
    uploaded = await client.post("/documents/upload", files={"file": ("fixture.pdf", b"%PDF-test", "application/pdf")})
    document_id = uploaded.json()["document"]["id"]
    assert (await client.get(f"/documents/{document_id}/spans")).json() == []
    service = DocumentProcessingService(db_session)
    normalized = Normalizer().normalize(fixture_output())
    service._persist_normalized_output(document_id, normalized)
    db_session.commit()
    first = (await client.get(f"/documents/{document_id}/spans")).json()
    assert len(first) == 3
    service._persist_normalized_output(document_id, normalized)
    db_session.commit()
    second = (await client.get(f"/documents/{document_id}/spans")).json()
    assert {item["id"] for item in first} == {item["id"] for item in second}
    assert (await client.get(f"/documents/{document_id}/spans?page_number=2")).json() == []
    title = next(item for item in first if item["text"] == "Bài học tiếng Việt")
    assert len((await client.get(f"/documents/{document_id}/spans?block_id={title['block_id']}")).json()) == 1
    normalized["blocks"][1]["spans"] = []
    service._persist_normalized_output(document_id, normalized)
    db_session.commit()
    assert len(db_session.scalars(select(Span)).all()) == 1
    from app.models.document import Document
    db_session.get(Document, document_id).status = "parsed"
    db_session.commit()
    assert (await client.delete(f"/documents/{document_id}")).status_code == 204
    assert db_session.scalars(select(Span)).all() == []


def test_span_migration_upgrade_downgrade(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect
    from app.core.config import get_settings
    url = f"sqlite:///{(tmp_path / 'migration.db').as_posix()}"
    monkeypatch.setattr(get_settings(), "database_url", url)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(url)
    assert "spans" in inspect(engine).get_table_names()
    command.downgrade(config, "202606270001")
    assert "spans" not in inspect(engine).get_table_names()
    command.upgrade(config, "head")
    assert "spans" in inspect(engine).get_table_names()
    engine.dispose()
