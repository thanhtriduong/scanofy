from app.services.file_profiler import FileProfiler
from app.services.normalizer import Normalizer
from app.services.router import DocumentRouter


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
