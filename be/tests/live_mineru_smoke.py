"""Opt-in real CLI/API smoke, isolated SQLite/storage; no Neon writes.

Run from be: .venv/Scripts/python.exe -m tests.live_mineru_smoke
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from uuid import uuid4

import httpx
from tests.pdf_fixtures import write_pdf


def main():
    root = Path(__file__).resolve().parents[2] / "tmp" / f"mineru-smoke-{uuid4()}"
    root.mkdir(parents=True)
    source = root / "synthetic-lesson.pdf"
    write_pdf(source)
    os.environ.update(DATABASE_URL=f"sqlite:///{(root / 'smoke.db').as_posix()}",
                      UPLOAD_DIR=str(root / "uploads"), MINERU_OUTPUT_DIR=str(root / "outputs"))
    from alembic import command
    from alembic.config import Config
    command.upgrade(Config("alembic.ini"), "head")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    log = (root / "server.log").open("w", encoding="utf-8")
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)], env=os.environ.copy(), stdout=log, stderr=log)
    url = f"http://127.0.0.1:{port}"
    result = {"root": str(root), "source": "synthetic single-page PDF", "real_mineru": True}
    try:
        with httpx.Client(base_url=url, timeout=20) as client:
            for _ in range(40):
                try:
                    if client.get("/health").is_success:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.5)
            started = time.monotonic()
            response = client.post("/documents/upload", files={"file": (source.name, source.read_bytes(), "application/pdf")})
            response.raise_for_status()
            document_id = response.json()["document"]["id"]
            result["upload_response_seconds"] = round(time.monotonic() - started, 3)
            result["original_readable_while_processing"] = client.get(f"/documents/{document_id}/file").status_code == 200
            observed = []
            for _ in range(950):
                status = client.get(f"/documents/{document_id}/status").json()
                state = status["status"]
                if not observed or observed[-1] != state:
                    observed.append(state)
                    print(f"state={state}", flush=True)
                if state in {"parsed", "failed", "awaiting_ocr"}:
                    break
                time.sleep(1)
            result["states"] = observed
            result["status"] = state
            if state != "parsed":
                # Keep engine diagnostics local, not in public report artifacts.
                (root / "failure.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
                raise RuntimeError("Live parsing did not reach parsed; diagnostics retained in isolated smoke directory.")
            for key in ("pages", "blocks", "spans"):
                data = client.get(f"/documents/{document_id}/{key}")
                data.raise_for_status()
                result[key] = len(data.json())
            assert result["pages"] == 1 and result["blocks"] > 0 and result["spans"] > 0
            preview = client.get(f"/documents/{document_id}/preview")
            preview.raise_for_status()
            result["preview_parse_run"] = bool(preview.json()["parse_run_id"])
            outputs = client.get(f"/documents/{document_id}/ocr-output").json()
            meta = outputs[0]["raw_output"]["_scanofy"]
            artifact = client.get(f"/documents/{document_id}/outputs/{outputs[0]['id']}/artifacts/{meta['markdown_artifact']}")
            assert artifact.status_code == 200
            result["markdown_artifact_readable"] = True
            result["artifact_count"] = len(meta["artifacts"])
            result["source_version"] = meta["source_version"]
            from app.db.session import SessionLocal
            from app.commands.renormalize import renormalize
            before = client.get(f"/documents/{document_id}/spans").json()
            with SessionLocal() as db:
                dry = renormalize(db, document_id, reprofile=True)
                assert not dry["applied"]
                renormalize(db, document_id, apply=True, reprofile=True)
            after = client.get(f"/documents/{document_id}/spans").json()
            assert {span["id"] for span in before} == {span["id"] for span in after}
            result["renormalize_preserves_span_ids"] = True
            result["elapsed_seconds"] = round(time.monotonic() - started, 3)
            (root / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(result, ensure_ascii=True), flush=True)
    finally:
        process.terminate()
        process.wait(timeout=15)
        log.close()


if __name__ == "__main__":
    main()
