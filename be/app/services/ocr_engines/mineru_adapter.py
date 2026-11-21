import asyncio
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from app.core.config import get_settings
from app.services.ocr_engines.base import OCRAdapter


class MinerUAdapter(OCRAdapter):
    engine_name = "mineru"

    async def parse(self, file_path: Path) -> dict:
        return await asyncio.to_thread(self._parse_sync, file_path)

    def _parse_sync(self, file_path: Path) -> dict:
        settings = get_settings()
        if not settings.mineru_enabled:
            raise RuntimeError("MinerU is disabled. Set MINERU_ENABLED=true to enable it.")

        mineru_executable = self._resolve_executable(settings.mineru_command)
        if mineru_executable is None:
            raise RuntimeError(
                f"MinerU CLI '{settings.mineru_command}' was not found. Install "
                "mineru[all]==4.2.3 or set MINERU_COMMAND to mineru-kit.exe."
            )

        output_dir = settings.mineru_output_root / file_path.parent.name
        output_dir.mkdir(parents=True, exist_ok=True)
        archive_path = output_dir / "mineru_output.zip"

        command = [
            mineru_executable,
            "parse",
            str(file_path),
            "--output",
            str(archive_path),
            "--format",
            "zip",
            "--ocr-mode",
            settings.mineru_ocr_mode,
        ]

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=settings.mineru_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"MinerU timed out after {settings.mineru_timeout_seconds} seconds."
            ) from exc

        stdout_text = process.stdout or ""
        stderr_text = process.stderr or ""
        if process.returncode != 0:
            details = stderr_text.strip() or stdout_text.strip() or "No CLI output was captured."
            raise RuntimeError(
                f"MinerU failed with exit code {process.returncode}: {details}"
            )

        if not archive_path.is_file():
            raise RuntimeError(
                f"MinerU completed without creating the expected archive: {archive_path}"
            )

        artifact_dir = output_dir / "artifacts"
        shutil.rmtree(artifact_dir, ignore_errors=True)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        self._extract_archive(archive_path, artifact_dir)

        markdown_path = self._preferred_file(artifact_dir, "markdown.md", "*.md")
        json_path = self._preferred_file(artifact_dir, "middle_json.json", "*.json")
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

    def _resolve_executable(self, command: str) -> str | None:
        resolved = shutil.which(command)
        if resolved is not None:
            return resolved

        command_path = Path(command)
        if command_path.is_absolute() or command_path.parent != Path("."):
            return None

        scripts_dir = Path(sys.executable).resolve().parent
        candidates = [scripts_dir / command, scripts_dir / f"{command}.exe"]
        return next((str(candidate) for candidate in candidates if candidate.is_file()), None)

    def _extract_archive(self, archive_path: Path, destination: Path) -> None:
        destination_root = destination.resolve()
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                target = (destination / member.filename).resolve()
                if not target.is_relative_to(destination_root):
                    raise RuntimeError(
                        f"MinerU archive contains an unsafe path: {member.filename}"
                    )
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)

    def _preferred_file(self, root: Path, filename: str, pattern: str) -> Path | None:
        exact_matches = sorted(root.rglob(filename))
        return exact_matches[0] if exact_matches else self._find_first(root, pattern)

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
