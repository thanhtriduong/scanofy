import subprocess
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.ocr_engines import mineru_adapter as adapter_module
from app.services.ocr_engines.mineru_adapter import MinerUAdapter
from app.services.normalizer import Normalizer


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
        if command[-1] == "--version":
            return subprocess.CompletedProcess(command, 0, "MinerU version: 4.2.3", "")
        captured_command.extend(command)
        archive_path = Path(command[command.index("--output") + 1])
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("markdown.md", "# Bài học")
            archive.writestr("middle_json.json", '{"pages": [{"page_idx": 0, "blocks": []}]}')
            archive.writestr("structured_content.json", "{}")
        return subprocess.CompletedProcess(command, 0, "Parsed 1 input(s).", "")

    monkeypatch.setattr(adapter_module.subprocess, "run", fake_run)

    result = await MinerUAdapter().parse(source_path)

    assert captured_command[:3] == [str(executable), "parse", str(source_path)]
    assert captured_command[-4:] == ["--format", "zip", "--ocr-mode", "auto"]
    assert result["markdown_output"] == "# Bài học"
    assert result["raw_output"]["pages"][0]["page_idx"] == 0
    assert result["raw_output"]["_scanofy"]["source_sha256"]
    assert result["raw_output"]["_scanofy"]["source_version"] == "4.2.3"
    assert result["raw_output"]["_scanofy"]["json_artifact"].endswith("middle_json.json")
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


def test_artifact_loader_rejects_missing_ambiguous_and_corrupt_output(tmp_path):
    adapter = MinerUAdapter()
    (tmp_path / "unrelated.json").write_text("{}")
    with pytest.raises(RuntimeError, match="middle_json"):
        adapter.load_artifacts(tmp_path)
    (tmp_path / "middle_json.json").write_text("not json")
    (tmp_path / "markdown.md").write_text("text")
    with pytest.raises(RuntimeError, match="UTF-8/JSON"):
        adapter.load_artifacts(tmp_path)
    (tmp_path / "middle_json.json").write_text('{"pages": []}')
    with pytest.raises(RuntimeError, match="empty"):
        adapter.load_artifacts(tmp_path)
    nested = tmp_path / "duplicate"
    nested.mkdir()
    (nested / "middle_json.json").write_text("{}")
    with pytest.raises(RuntimeError, match="found 2"):
        adapter.load_artifacts(tmp_path)


def test_archive_rejects_path_traversal(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("../escape.txt", "unsafe")
    with pytest.raises(RuntimeError, match="unsafe path"):
        MinerUAdapter()._extract_archive(archive, tmp_path / "artifacts")
    assert not (tmp_path / "escape.txt").exists()


def test_real_mineru_423_artifact_normalizes_without_model(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "mineru_v4_smoke_middle.json"
    (tmp_path / "middle_json.json").write_bytes(fixture.read_bytes())
    (tmp_path / "markdown.md").write_text("This is a digital educational document with selectable text.", encoding="utf-8")
    artifacts = MinerUAdapter().load_artifacts(tmp_path)
    normalized = Normalizer().normalize({"engine": "mineru", "raw_output": artifacts["raw_output"]})
    assert len(normalized["pages"]) == 1
    assert len(normalized["blocks"]) == 1
    block = normalized["blocks"][0]
    assert block["bbox"] == [0.046, 0.111, 0.566, 0.13]
    assert len(block["spans"]) == 1
    assert block["spans"][0]["text"] == block["text"]
