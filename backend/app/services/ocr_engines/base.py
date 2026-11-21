from abc import ABC, abstractmethod
from pathlib import Path


class OCRAdapter(ABC):
    engine_name: str

    @abstractmethod
    async def parse(self, file_path: Path) -> dict:
        """Parse a document into raw OCR/parser output."""
