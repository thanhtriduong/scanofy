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
    assert normalized["blocks"][0]["block_type"] == "paragraph_title"
    assert normalized["blocks"][0]["bbox"] == [0.1, 0.2, 0.8, 0.3]
    assert normalized["blocks"][0]["raw_json"]["coordinate_system"] == "normalized_0_1"
