import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from PIL import Image, ImageDraw
import pytest
from sqlalchemy import select

from app.commands.paddle_worker import raster_pages
from app.commands.renormalize import renormalize
from app.core.config import get_settings
from app.models.document import Document
from app.models.document_job import DocumentJob
from app.models.span import Span
from app.schemas.normalized import NormalizedDocument
from app.services.document_processing import DocumentProcessingService
from app.services.engine_orchestrator import default_orchestrator
from app.services.ocr_engines import paddleocr_adapter as adapter_module
from app.services.ocr_engines.paddleocr_adapter import PaddleOCRAdapter
from app.services.paddleocr_normalizer import normalize_paddle_output, validate_paddle_output


def raw_output():
    return {"schema": "scanofy.paddleocr.v1", "metadata": {"paddleocr_version": "3.3.2"}, "pages": [
        {"page_number": 1, "width": 200, "height": 100, "result": {
            "rec_texts": ["Tài liệu tiếng Việt"], "rec_scores": [0.95],
            "rec_polys": [[[20, 10], [180, 10], [180, 30], [20, 30]]],
        }},
    ]}


def test_paddle_normalizer_preserves_text_confidence_polygon_and_blank_page():
    raw = raw_output()
    raw["pages"].append({"page_number": 2, "width": 100, "height": 100,
                         "result": {"rec_texts": [], "rec_scores": [], "rec_polys": []}})
    normalized = NormalizedDocument.model_validate(normalize_paddle_output({"raw_output": raw}))
    assert len(normalized.pages) == 2 and len(normalized.blocks) == 1
    block = normalized.blocks[0]
    assert block.bbox == [0.1, 0.1, 0.9, 0.3]
    assert block.spans[0].text == "Tài liệu tiếng Việt"
    assert block.spans[0].bbox == block.bbox
    assert block.confidence == 0.95
    assert block.is_handwritten is None and block.quality_score is None


@pytest.mark.parametrize("polygon", [[], [[-2, 0], [20, 0], [20, 20], [0, 20]], [[0, 0]] * 4])
def test_invalid_geometry_stays_null_with_review(polygon):
    raw = raw_output()
    raw["pages"][0]["result"]["rec_polys"] = [polygon]
    normalized = normalize_paddle_output({"raw_output": raw})
    block = normalized["blocks"][0]
    assert block["bbox"] is None and block["needs_review"]


@pytest.mark.parametrize("key,value", [("rec_scores", []), ("rec_polys", []), ("rec_scores", [float("nan")]), ("rec_scores", [1.1])])
def test_paddle_raw_rejects_misaligned_or_invalid_confidence(key, value):
    raw = raw_output()
    raw["pages"][0]["result"][key] = value
    with pytest.raises(ValueError):
        validate_paddle_output(raw)


def test_pdf_raster_matches_cropbox_and_native_rotation(tmp_path):
    from pypdf import PdfReader, PdfWriter
    image = Image.new("RGB", (120, 80), "white")
    ImageDraw.Draw(image).rectangle((20, 20, 30, 30), fill="red")
    source = tmp_path / "source.pdf"
    image.save(source, "PDF", resolution=72)
    reader = PdfReader(source)
    page = reader.pages[0]
    page.cropbox.lower_left = (10, 10)
    page.cropbox.upper_right = (110, 70)
    page.rotate(90)
    writer = PdfWriter()
    writer.add_page(page)
    target = tmp_path / "rotated.pdf"
    writer.write(target)
    pages = list(raster_pages(target, tmp_path, 144, 10, 100_000))
    assert pages[0][2] == (120, 200)
    with Image.open(pages[0][1]) as rendered:
        red, green, blue = rendered.getpixel((90, 30))
        assert red > 200 and green < 80 and blue < 80
    assert pages[0][3]["coordinate_frame"] == "cropbox_with_native_rotation"
    with pytest.raises(ValueError, match="MAX_PIXELS"):
        list(raster_pages(target, tmp_path, 144, 10, 100))


def test_image_raster_applies_exif_and_pixel_limit(tmp_path):
    source = tmp_path / "image.jpg"
    image = Image.new("RGB", (120, 80), "white")
    exif = image.getexif()
    exif[274] = 6
    image.save(source, exif=exif)
    assert list(raster_pages(source, tmp_path, 144, 10, 100_000))[0][2] == (80, 120)
    with pytest.raises(ValueError, match="MAX_PIXELS"):
        list(raster_pages(source, tmp_path, 144, 10, 100))


@pytest.mark.anyio
async def test_adapter_keeps_per_run_artifacts_and_uses_bounded_worker(tmp_path, monkeypatch):
    source = tmp_path / "document" / "original.png"
    source.parent.mkdir()
    source.write_bytes(b"synthetic image")
    settings = get_settings()
    monkeypatch.setattr(settings, "ocr_output_dir", tmp_path / "outputs")
    monkeypatch.setattr(settings, "paddleocr_enabled", True)
    def fake_run(command, **kwargs):
        assert kwargs["timeout"] == settings.paddleocr_timeout_seconds
        assert command[1:3] == ["-m", "app.commands.paddle_worker"]
        output = Path(command[command.index("--output") + 1])
        (output / "paddleocr.json").write_text(json.dumps(raw_output()), encoding="utf-8")
        (output / "markdown.md").write_text("Tài liệu tiếng Việt", encoding="utf-8")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(adapter_module.subprocess, "run", fake_run)
    first = await PaddleOCRAdapter().parse(source)
    second = await PaddleOCRAdapter().parse(source)
    meta = first["raw_output"]["_scanofy"]
    assert meta["storage_kind"] == "ocr" and len(meta["source_sha256"]) == 64
    assert meta["json_artifact"] != second["raw_output"]["_scanofy"]["json_artifact"]
    assert (settings.ocr_output_root / source.parent.name / meta["json_artifact"]).is_file()
    assert first["average_confidence"] == 0.95


@pytest.mark.anyio
async def test_adapter_reports_worker_timeout(tmp_path, monkeypatch):
    source = tmp_path / "doc" / "original.png"
    source.parent.mkdir()
    source.touch()
    monkeypatch.setattr(get_settings(), "ocr_output_dir", tmp_path / "outputs")
    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])
    monkeypatch.setattr(adapter_module.subprocess, "run", timeout)
    with pytest.raises(RuntimeError, match="timed out"):
        await PaddleOCRAdapter().parse(source)


def test_image_pipeline_and_renormalize_keep_span_ids(db_session, tmp_path, monkeypatch):
    source = tmp_path / "image.png"
    Image.new("RGB", (200, 100), "white").save(source)
    document = Document(filename=source.name, file_type="png", storage_url=str(source), status="uploaded")
    db_session.add(document)
    db_session.flush()
    job = DocumentJob(document_id=document.id, status="queued")
    db_session.add(job)
    db_session.commit()
    orchestrator = default_orchestrator()
    async def parse(_path):
        return {"engine": "paddleocr", "status": "completed", "raw_output": raw_output()}
    monkeypatch.setattr(orchestrator.registry.require("paddleocr").adapter, "parse", parse)
    DocumentProcessingService(db_session, orchestrator).run_pipeline(document.id, job.id, source)
    assert document.status == "parsed" and document.router_decision["engine"] == "paddleocr"
    before = {span.id for span in db_session.scalars(select(Span)).all()}
    assert len(before) == 1
    assert not renormalize(db_session, document.id)["applied"]
    renormalize(db_session, document.id, apply=True)
    assert {span.id for span in db_session.scalars(select(Span)).all()} == before


@pytest.mark.anyio
async def test_adapter_disabled_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "paddleocr_enabled", False)
    with pytest.raises(RuntimeError, match="disabled"):
        await PaddleOCRAdapter().parse(tmp_path / "unused.png")
