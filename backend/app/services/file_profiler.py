from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class FileProfile:
    file_type: str
    size_bytes: int
    text_layer_ratio: float
    scan_score: float
    handwriting_score: float
    page_count: int | None = None


class FileProfiler:
    """Week 1 placeholder profiler.

    Real PDF/DOCX/image inspection arrives in Week 2. This stub records enough
    metadata for routing and status endpoints without invoking OCR.
    """

    def profile(self, file_path: Path, file_type: str) -> dict:
        file_type = file_type.lower().lstrip(".")
        size_bytes = file_path.stat().st_size
        likely_text_file = file_type in {"pdf", "docx"}
        profile = FileProfile(
            file_type=file_type,
            size_bytes=size_bytes,
            text_layer_ratio=0.7 if likely_text_file else 0.0,
            scan_score=0.0 if likely_text_file else 0.6,
            handwriting_score=0.0,
        )
        return asdict(profile)
