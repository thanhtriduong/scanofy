import subprocess
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.ocr_engines import mineru_adapter as adapter_module
from app.services.ocr_engines.mineru_adapter import MinerUAdapter


def test_mineru_adapter_finds_cli_beside_active_python(tmp_path, monkeypatch) -> None:
    scripts_dir = tmp_path / "Scripts"
    scripts_dir.mkdir()
    python_executable = scripts_dir / "python.exe"
    mineru_executable = scripts_dir / "mineru-kit.exe"
    python_executable.touch()
    mineru_executable.touch()
    monkeypatch.setattr(adapter_module.shutil, "which", lambda _command: None)
    monkeypatch.setattr(adapter_module.sys, "executable", str(python_executable))

    resolved = MinerUAdapter()._resolve_executable("mineru-kit")

    assert resolved == str(mineru_executable)


@pytest.mark.anyio
async def test_mineru_adapter_uses_v4_kit_cli_and_extracts_artifacts(
    tmp_path, monkeypatch
) -> None:
    document_dir = tmp_path / "document-1"
    document_dir.mkdir()
    source_path = document_dir / "original.pdf"
    source_path.write_bytes(b"%PDF-1.4 test")
    output_root = tmp_path / "mineru_outputs"
    executable = tmp_path / "mineru-kit.exe"
    executable.touch()
    settings = SimpleNamespace(
        mineru_enabled=True,
        mineru_command=str(executable),
        mineru_output_root=output_root,
        mineru_ocr_mode="auto",
        mineru_timeout_seconds=30,
    )
    captured_command: list[str] = []

    monkeypatch.setattr(adapter_module, "get_settings", lambda: settings)
    monkeypatch.setattr(adapter_module.shutil, "which", lambda command: command)

    def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess:
        captured_command.extend(command)
        archive_path = Path(command[command.index("--output") + 1])
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("markdown.md", "# Bài học")
            archive.writestr("middle_json.json", '{"pages": [{"page_no": 0}]}')
            archive.writestr("structured_content.json", "{}")
        return subprocess.CompletedProcess(command, 0, "Parsed 1 input(s).", "")

    monkeypatch.setattr(adapter_module.subprocess, "run", fake_run)

    result = await MinerUAdapter().parse(source_path)

    assert captured_command[:3] == [str(executable), "parse", str(source_path)]
    assert captured_command[-4:] == ["--format", "zip", "--ocr-mode", "auto"]
    assert result["markdown_output"] == "# Bài học"
    assert result["raw_output"]["pages"][0]["page_no"] == 0
    assert Path(result["markdown_path"]).name == "markdown.md"
    assert Path(result["json_path"]).name == "middle_json.json"


@pytest.mark.anyio
async def test_mineru_adapter_reports_cli_output_on_failure(tmp_path, monkeypatch) -> None:
    source_path = tmp_path / "document-2" / "original.pdf"
    source_path.parent.mkdir()
    source_path.write_bytes(b"%PDF-1.4 test")
    settings = SimpleNamespace(
        mineru_enabled=True,
        mineru_command="mineru-kit",
        mineru_output_root=tmp_path / "mineru_outputs",
        mineru_ocr_mode="auto",
        mineru_timeout_seconds=30,
    )

    monkeypatch.setattr(adapter_module, "get_settings", lambda: settings)
    monkeypatch.setattr(adapter_module.shutil, "which", lambda _command: "mineru-kit.exe")
    monkeypatch.setattr(
        adapter_module.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(
            command, 2, "", "model initialization failed"
        ),
    )

    with pytest.raises(RuntimeError, match="model initialization failed"):
        await MinerUAdapter().parse(source_path)
