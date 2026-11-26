"""Resolve only configured storage roots; never accept a root path from OCR data."""
from app.core.config import get_settings


def artifact_root(raw_output: dict):
    settings = get_settings()
    kind = raw_output.get("_scanofy", {}).get("storage_kind", "legacy_mineru")
    if kind == "ocr":
        return settings.ocr_output_root
    if kind == "legacy_mineru":
        return settings.mineru_output_root
    raise ValueError("Unknown OCR artifact storage kind.")
