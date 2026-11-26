"""Opt-in real PaddleOCR HTTP smoke on synthetic Vietnamese image and scanned PDF."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from uuid import uuid4

import httpx
from PIL import Image, ImageDraw, ImageFont


def main():
    root = Path(__file__).resolve().parents[2] / "tmp" / f"paddleocr-smoke-{uuid4()}"
    root.mkdir(parents=True)
    image = Image.new("RGB", (1200, 600), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 42)
    draw.text((60, 90), "SCANOFY - Tài liệu giáo dục", font=font, fill="black")
    draw.text((60, 180), "Học tập và nhận dạng văn bản tiếng Việt.", font=font, fill="black")
    draw.text((60, 270), "Trang kiểm thử OCR 12345", font=font, fill="black")
    source_image = root / "synthetic-vietnamese.png"
    source_pdf = root / "synthetic-scan.pdf"
    image.save(source_image)
    image.save(source_pdf, "PDF", save_all=True, append_images=[image], resolution=144)
    os.environ.update(DATABASE_URL=f"sqlite:///{(root / 'smoke.db').as_posix()}",
                      UPLOAD_DIR=str(root / "uploads"), OCR_OUTPUT_DIR=str(root / "outputs"),
                      MINERU_OUTPUT_DIR=str(root / "mineru-outputs"), PADDLEOCR_ENABLED="true")
    from alembic import command
    from alembic.config import Config
    command.upgrade(Config("alembic.ini"), "head")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    log = (root / "server.log").open("w", encoding="utf-8")
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
                               env=os.environ.copy(), stdout=log, stderr=log)
    summary = {"root": str(root), "real_paddleocr": True, "documents": []}
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=20) as client:
            for _ in range(40):
                try:
                    if client.get("/health").is_success:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.5)
            for source, mime, expected_pages in ((source_image, "image/png", 1), (source_pdf, "application/pdf", 2)):
                started = time.monotonic()
                response = client.post("/documents/upload", files={"file": (source.name, source.read_bytes(), mime)})
                response.raise_for_status()
                document_id = response.json()["document"]["id"]
                assert client.get(f"/documents/{document_id}/file").is_success
                for _ in range(950):
                    status = client.get(f"/documents/{document_id}/status").json()
                    if status["status"] in {"parsed", "failed", "awaiting_ocr"}:
                        break
                    time.sleep(1)
                if status["status"] != "parsed":
                    (root / "failure.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
                    raise RuntimeError(f"PaddleOCR smoke failed; diagnostics in {root}")
                pages = client.get(f"/documents/{document_id}/pages").json()
                blocks = client.get(f"/documents/{document_id}/blocks").json()
                spans = client.get(f"/documents/{document_id}/spans").json()
                assert len(pages) == expected_pages and len(blocks) >= expected_pages and len(spans) >= len(blocks)
                assert all(b["source_engine"] == "paddleocr" for b in blocks)
                assert all(b["bbox"] and b["coordinate_system"] == "normalized_0_1" for b in blocks)
                assert "scanofy" in " ".join(b["text"] or "" for b in blocks).lower()
                preview = client.get(f"/documents/{document_id}/preview")
                preview.raise_for_status()
                assert len(preview.json()["pages"]) == expected_pages
                assert all(block["coordinate_system"] == "normalized_0_1" for block in preview.json()["blocks"])
                outputs = client.get(f"/documents/{document_id}/ocr-output").json()
                output = outputs[0]
                meta = output["raw_output"]["_scanofy"]
                for path in (meta["markdown_artifact"], meta["json_artifact"]):
                    assert client.get(f"/documents/{document_id}/outputs/{output['id']}/artifacts/{path}").is_success
                document_root = root / "outputs" / document_id
                assert document_root.is_dir()
                assert client.delete(f"/documents/{document_id}").status_code == 204
                assert not document_root.exists()
                summary["documents"].append({"input": source.suffix, "pages": len(pages), "blocks": len(blocks),
                    "spans": len(spans), "elapsed_seconds": round(time.monotonic() - started, 3),
                    "preview_artifacts_delete": True, "paddleocr_version": meta["source_version"]})
                print(json.dumps(summary["documents"][-1]), flush=True)
        (root / "result.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary), flush=True)
    finally:
        process.terminate()
        process.wait(timeout=15)
        log.close()


if __name__ == "__main__":
    main()
