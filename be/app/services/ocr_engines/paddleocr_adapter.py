import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from app.core.config import BE_ROOT, get_settings
from app.services.ocr_engines.base import OCRAdapter
from app.services.paddleocr_normalizer import validate_paddle_output


class PaddleOCRAdapter(OCRAdapter):
    engine_name = "paddleocr"

    async def parse(self, file_path: Path) -> dict:
        return await asyncio.to_thread(self._parse_sync, file_path)

    def _parse_sync(self, file_path: Path) -> dict:
        settings = get_settings()
        if not settings.paddleocr_enabled:
            raise RuntimeError("PaddleOCR is disabled. Set PADDLEOCR_ENABLED=true to enable it.")
        root = settings.ocr_output_root / file_path.parent.name
        run_dir = root / str(uuid4())
        run_dir.mkdir(parents=True)
        command = [sys.executable, "-m", "app.commands.paddle_worker", "--input", str(file_path.resolve()),
                   "--output", str(run_dir), "--lang", settings.paddleocr_lang,
                   "--dpi", str(settings.paddleocr_render_dpi), "--max-pages", str(settings.paddleocr_max_pages),
                   "--max-pixels", str(settings.paddleocr_max_pixels)]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        # Keep optional model downloads inside the workspace, shared across runs.
        env["PADDLE_PDX_CACHE_HOME"] = str(BE_ROOT / "storage" / "model_cache" / "paddleocr")
        log_path = run_dir / "worker.log"
        with log_path.open("w", encoding="utf-8") as log:
            try:
                process = subprocess.run(command, cwd=BE_ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                         timeout=settings.paddleocr_timeout_seconds, check=False)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(f"PaddleOCR timed out after {settings.paddleocr_timeout_seconds} seconds.") from exc
        if process.returncode:
            details = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
            raise RuntimeError(f"PaddleOCR worker failed ({process.returncode}): {details}")
        try:
            raw = json.loads((run_dir / "paddleocr.json").read_text(encoding="utf-8"))
            markdown = (run_dir / "markdown.md").read_text(encoding="utf-8")
        except (OSError, ValueError) as exc:
            raise RuntimeError("PaddleOCR worker did not produce valid artifacts.") from exc
        validate_paddle_output(raw)
        raw["_scanofy"] = {
            "storage_kind": "ocr", "source_engine": self.engine_name,
            "source_version": raw["metadata"]["paddleocr_version"],
            "source_sha256": hashlib.sha256(file_path.read_bytes()).hexdigest(),
            "json_artifact": (run_dir / "paddleocr.json").relative_to(root).as_posix(),
            "markdown_artifact": (run_dir / "markdown.md").relative_to(root).as_posix(),
            "artifacts": [{"path": path.relative_to(root).as_posix(), "size_bytes": path.stat().st_size}
                          for path in sorted(run_dir.rglob("*")) if path.is_file() and path != log_path],
        }
        scores = [score for page in raw["pages"] for score in page["result"]["rec_scores"]]
        return {"engine": self.engine_name, "status": "completed", "raw_output": raw,
                "markdown_output": markdown, "average_confidence": sum(scores) / len(scores) if scores else None}
