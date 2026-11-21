import asyncio
import json
import shutil
from pathlib import Path

from app.core.config import get_settings
from app.services.ocr_engines.base import OCRAdapter


class MinerUAdapter(OCRAdapter):
    engine_name = "mineru"

    async def parse(self, file_path: Path) -> dict:
        settings = get_settings()
        if not settings.mineru_enabled:
            raise RuntimeError("MinerU is disabled. Set MINERU_ENABLED=true to enable it.")

        mineru_executable = shutil.which(settings.mineru_command)
        if mineru_executable is None:
            raise RuntimeError(
                "MinerU CLI was not found. Install MinerU in a supported Python 3.10-3.13 "
                "environment and make the 'mineru' command available on PATH."
            )

        output_dir = settings.mineru_output_root / file_path.parent.name
        output_dir.mkdir(parents=True, exist_ok=True)

        command = [
            mineru_executable,
            "-p",
            str(file_path),
            "-o",
            str(output_dir),
            "-b",
            settings.mineru_backend,
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=settings.mineru_timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.communicate()
            raise RuntimeError(
                f"MinerU timed out after {settings.mineru_timeout_seconds} seconds."
            ) from exc

        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")
        if process.returncode != 0:
            raise RuntimeError(f"MinerU failed with exit code {process.returncode}: {stderr_text}")

        markdown_path = self._find_first(output_dir, "*.md")
        json_path = self._find_first(output_dir, "*.json")
        markdown_output = markdown_path.read_text(encoding="utf-8", errors="replace") if markdown_path else None
        raw_output = self._read_json(json_path) if json_path else {}

        return {
            "engine": self.engine_name,
            "file_path": str(file_path),
            "status": "completed",
            "output_dir": str(output_dir),
            "markdown_path": str(markdown_path) if markdown_path else None,
            "json_path": str(json_path) if json_path else None,
            "markdown_output": markdown_output,
            "raw_output": raw_output,
            "stdout": stdout_text,
            "stderr": stderr_text,
        }

    def _find_first(self, root: Path, pattern: str) -> Path | None:
        matches = sorted(root.rglob(pattern))
        return matches[0] if matches else None

    def _read_json(self, path: Path | None) -> dict:
        if path is None:
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            return {"unparsed_json_path": str(path)}
