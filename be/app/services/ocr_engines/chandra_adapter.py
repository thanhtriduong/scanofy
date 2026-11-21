from pathlib import Path

from app.services.ocr_engines.base import OCRAdapter


class ChandraAdapter(OCRAdapter):
    engine_name = "chandra"

    async def parse(self, file_path: Path) -> dict:
        return {
            "engine": self.engine_name,
            "file_path": str(file_path),
            "status": "placeholder",
            "message": "Chandra OCR integration is planned after Week 1.",
        }
