from app.services.file_profiler import FileProfiler
from app.services.normalizer import Normalizer
from app.services.router import DocumentRouter
import pytest
from sqlalchemy import select
from app.models.document import Document
from app.models.page import Page
from app.models.block import Block
from app.services.document_processing import DocumentProcessingService


@pytest.mark.parametrize("bbox", [[-1, 0, 1, 1], [0, 0, 500, 800], [0.8, 0.1, 0.2, 0.9], [0, 0, float("nan"), 1], [True, 0, 1, 1]])
def test_normalizer_rejects_unknown_or_invalid_geometry(bbox):
    assert Normalizer()._valid_bbox(bbox) is None


def test_repeated_normalization_preserves_ids_and_updates_content(db_session):
    document = Document(filename="lesson.pdf", file_type="pdf", storage_url="unused", status="normalizing")
    db_session.add(document)
    db_session.commit()
    normalized = Normalizer().normalize({"engine": "mineru", "raw_output": {"pages": [{"page_idx": 0, "blocks": [{"type": "text", "index": 0, "bbox": [0.1, 0.1, 0.9, 0.2], "content": "Original"}]}]}})
    service = DocumentProcessingService(db_session)
    service._persist_normalized_output(document.id, normalized)
    db_session.commit()
    first_id = db_session.scalars(select(Block)).one().id
    normalized["blocks"][0]["text"] = "Updated"
    service._persist_normalized_output(document.id, normalized)
    db_session.commit()
    assert len(db_session.scalars(select(Page)).all()) == 1
    block = db_session.scalars(select(Block)).one()
    assert block.id == first_id
    assert block.text == "Updated"


def test_pipeline_publishes_parsed_output_after_normalization(db_session, tmp_path, monkeypatch):
    from app.models.document_job import DocumentJob
    from app.models.ocr_output import OCROutput
    source = tmp_path / "lesson.pdf"
    source.write_bytes(b"%PDF-1.4 test")
    document = Document(filename="lesson.pdf", file_type="pdf", storage_url=str(source), status="uploaded")
    db_session.add(document)
    db_session.flush()
    job = DocumentJob(document_id=document.id, status="queued")
    db_session.add(job)
    db_session.commit()
    async def fake_parse(_path):
        return {"engine": "mineru", "raw_output": {"pages": [{"page_idx": 0, "blocks": [{"type": "text", "index": 0, "bbox": [0, 0, 1, 1], "content": "Bài học"}]}]}}
    service = DocumentProcessingService(db_session)
    monkeypatch.setattr(service.mineru, "parse", fake_parse)
    service.run_placeholder_pipeline(document.id, job.id, source)
    assert document.status == "parsed"
    assert job.status == "completed"
    assert db_session.scalars(select(Page)).one().page_number == 1
    assert db_session.scalars(select(Block)).one().text == "Bài học"
    assert db_session.scalars(select(OCROutput)).one().engine == "mineru"


def test_profiler_records_basic_pdf_metadata(tmp_path) -> None:
    file_path = tmp_path / "lesson.pdf"
    file_path.write_bytes(b"%PDF-1.4 test")

    profile = FileProfiler().profile(file_path, "pdf")

    assert profile["file_type"] == "pdf"
    assert profile["size_bytes"] == file_path.stat().st_size
    assert profile["text_layer_ratio"] == 0.7


def test_router_selects_mineru_for_digital_pdf() -> None:
    decision = DocumentRouter().choose_engine(
        {
            "file_type": "pdf",
            "text_layer_ratio": 0.7,
            "scan_score": 0.0,
            "handwriting_score": 0.0,
        }
    )

    assert decision["engine"] == "mineru"


def test_normalizer_preserves_markdown_in_placeholder_block() -> None:
    normalized = Normalizer().normalize(
        {
            "engine": "mineru",
            "markdown_output": "# Bài học",
            "average_confidence": 0.9,
        }
    )

    assert normalized["status"] == "completed"
    assert normalized["pages"][0]["raw_text"] == "# Bài học"
    assert normalized["blocks"][0]["source_engine"] == "mineru"


def test_normalizer_maps_mineru_v4_pages_and_normalized_geometry() -> None:
    normalized = Normalizer().normalize(
        {
            "engine": "mineru",
            "raw_output": {
                "pages": [
                    {
                        "page_idx": 0,
                        "blocks": [
                            {
                                "type": "paragraph_title",
                                "index": 3,
                                "bbox": [0.1, 0.2, 0.8, 0.3],
                                "content": [
                                    {"type": "text", "content": "1 "},
                                    {"type": "text", "content": "Giới thiệu"},
                                ],
                            }
                        ],
                    }
                ]
            },
        }
    )

    assert normalized["pages"][0]["page_number"] == 1
    assert normalized["pages"][0]["raw_text"] == "1 Giới thiệu"
    assert normalized["blocks"][0]["block_type"] == "heading"
    assert normalized["blocks"][0]["bbox"] == [0.1, 0.2, 0.8, 0.3]
    assert normalized["blocks"][0]["raw_json"]["coordinate_system"] == "normalized_0_1"
