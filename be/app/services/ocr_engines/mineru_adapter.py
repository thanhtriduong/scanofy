import asyncio
import json
import shutil
import subprocess
import sys
import zipfile
import hashlib
import re
from uuid import uuid4
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

        # Retain each parse's artifacts; retries must not overwrite previous evidence.
        output_dir = settings.mineru_output_root / file_path.parent.name / str(uuid4())
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
        artifact_dir.mkdir(parents=True, exist_ok=True)
        self._extract_archive(archive_path, artifact_dir)
        artifacts = self.load_artifacts(artifact_dir)
        markdown_path = artifacts["markdown_path"]
        json_path = artifacts["json_path"]
        raw_output = artifacts["raw_output"]
        source_version = self._cli_version(mineru_executable)
        manifest = []
        for path in sorted(artifact_dir.rglob("*")):
            if path.is_file():
                manifest.append({"path": path.relative_to(settings.mineru_output_root / file_path.parent.name).as_posix(), "size_bytes": path.stat().st_size})
        raw_output["_scanofy"] = {
            "source_engine": "mineru", "source_version": source_version,
            "source_sha256": hashlib.sha256(file_path.read_bytes()).hexdigest(),
            "markdown_artifact": markdown_path.relative_to(settings.mineru_output_root / file_path.parent.name).as_posix(),
            "json_artifact": json_path.relative_to(settings.mineru_output_root / file_path.parent.name).as_posix(),
            "artifacts": manifest,
        }

        return {
            "engine": self.engine_name,
            "file_path": str(file_path),
            "status": "completed",
            "output_dir": str(output_dir),
            "markdown_path": str(markdown_path) if markdown_path else None,
            "json_path": str(json_path) if json_path else None,
            "markdown_output": artifacts["markdown_output"],
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

    def _cli_version(self, executable: str) -> str | None:
        try:
            result = subprocess.run([executable, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, check=False)
            match = re.search(r"MinerU version:\s*([\w.+-]+)", result.stdout or "")
            return match.group(1) if result.returncode == 0 and match else None
        except (OSError, subprocess.TimeoutExpired):
            return None

    def _extract_archive(self, archive_path: Path, destination: Path) -> None:
        destination_root = destination.resolve()
        with zipfile.ZipFile(archive_path) as archive:
            if len(archive.infolist()) > 10000 or sum(item.file_size for item in archive.infolist()) > 1024 * 1024 * 1024:
                raise RuntimeError("MinerU archive exceeds extraction limits (10000 files / 1 GiB).")
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

    def load_artifacts(self, root: Path) -> dict:
        """Accept only the supported v4 contract, never an arbitrary JSON file."""
        def required(filename: str) -> Path:
            matches = list(root.rglob(filename))
            if len(matches) != 1:
                raise RuntimeError(f"Expected exactly one MinerU {filename}; found {len(matches)}.")
            return matches[0]
        json_path = required("middle_json.json")
        markdown_path = required("markdown.md")
        try:
            raw = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
        except (ValueError, UnicodeError) as exc:
            raise RuntimeError("MinerU artifact is not valid UTF-8/JSON.") from exc
        self.validate_output(raw)
        return {"raw_output": raw, "markdown_output": markdown, "markdown_path": markdown_path, "json_path": json_path}

    @staticmethod
    def validate_output(raw: dict) -> None:
        if not isinstance(raw, dict) or not isinstance(raw.get("pages"), list) or not raw["pages"]:
            raise RuntimeError("Unsupported/empty MinerU output: expected non-empty pages[].")
        numbers = []
        for page in raw["pages"]:
            if not isinstance(page, dict) or type(page.get("page_idx")) is not int or page["page_idx"] < 0 or not isinstance(page.get("blocks"), list):
                raise RuntimeError("Invalid MinerU page: expected page_idx and blocks[].")
            if any(not isinstance(block, dict) for block in page["blocks"]):
                raise RuntimeError("Invalid MinerU block object.")
            numbers.append(page["page_idx"])
        if sorted(numbers) != list(range(len(numbers))):
            raise RuntimeError("MinerU pages must cover contiguous page_idx values starting at 0.")
