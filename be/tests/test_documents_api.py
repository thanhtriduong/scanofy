from pathlib import Path

import pytest

from app.core.config import get_settings
from app.models.ocr_output import OCROutput
from app.models.document import Document


@pytest.mark.anyio
async def test_paddle_preview_retains_canonical_geometry(client, db_session):
    document = Document(filename="scan.pdf", file_type="pdf", storage_url="unused", status="parsed")
    db_session.add(document)
    db_session.flush()
    raw = {"schema": "scanofy.paddleocr.v1", "pages": [{
        "page_number": 1, "width": 200, "height": 100,
        "result": {"rec_texts": ["Thông báo"], "rec_scores": [0.95],
                   "rec_polys": [[[20, 10], [180, 10], [180, 30], [20, 30]]]},
    }]}
    db_session.add(OCROutput(document_id=document.id, engine="paddleocr", raw_output=raw))
    db_session.commit()
    response = await client.get(f"/documents/{document.id}/preview")
    assert response.status_code == 200
    preview = response.json()
    assert preview["source_engine"] == "paddleocr"
    block = preview["blocks"][0]
    assert block["bbox"] == [0.1, 0.1, 0.9, 0.3]
    assert block["coordinate_system"] == "normalized_0_1"
    assert block["spans"][0]["coordinate_system"] == block["coordinate_system"]


@pytest.mark.anyio
async def test_preview_keeps_historical_markdown_output_readable(client, db_session):
    document = Document(filename="legacy.pdf", file_type="pdf", storage_url="unused", status="parsed")
    db_session.add(document)
    db_session.flush()
    db_session.add(OCROutput(document_id=document.id, engine="mineru", raw_output={"pdf_info": []}, markdown_output="# Legacy lesson"))
    db_session.commit()
    response = await client.get(f"/documents/{document.id}/preview")
    assert response.status_code == 200
    assert response.json()["blocks"][0]["text"] == "# Legacy lesson"


@pytest.mark.anyio
async def test_artifact_access_is_manifest_and_document_scoped(client, db_session):
    response = await client.post("/documents/upload", files={"file": ("sample.pdf", b"%PDF-test", "application/pdf")})
    document_id = response.json()["document"]["id"]
    artifact = get_settings().mineru_output_root / document_id / "run" / "markdown.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Synthetic lesson", encoding="utf-8")
    output = OCROutput(document_id=document_id, engine="mineru", raw_output={"_scanofy": {"artifacts": [{"path": "run/markdown.md"}]}})
    db_session.add(output)
    db_session.commit()
    url = f"/documents/{document_id}/outputs/{output.id}/artifacts"
    allowed = await client.get(f"{url}/run/markdown.md")
    assert allowed.status_code == 200
    assert allowed.headers["content-disposition"].startswith("attachment;")
    assert (await client.get(f"{url}/run/private.json")).status_code == 404
    assert (await client.get(f"/documents/another-document/outputs/{output.id}/artifacts/run/markdown.md")).status_code == 404


@pytest.mark.anyio
async def test_shared_ocr_artifacts_and_delete_preserve_legacy_support(client, db_session):
    document = Document(filename="scan.png", file_type="png", storage_url="unused", status="parsed")
    db_session.add(document)
    db_session.flush()
    settings = get_settings()
    for root in (settings.mineru_output_root, settings.ocr_output_root):
        artifact = root / document.id / "run" / "text.md"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("lesson", encoding="utf-8")
    output = OCROutput(document_id=document.id, engine="paddleocr", raw_output={"_scanofy": {
        "storage_kind": "ocr", "artifacts": [{"path": "run/text.md"}, {"path": "../../private.txt"}]}})
    db_session.add(output)
    db_session.commit()
    url = f"/documents/{document.id}/outputs/{output.id}/artifacts"
    assert (await client.get(f"{url}/run/text.md")).status_code == 200
    # Encoded traversal must not escape the configured document root, even if listed.
    assert (await client.get(f"{url}/%2E%2E/%2E%2E/private.txt")).status_code == 404
    assert (await client.delete(f"/documents/{document.id}")).status_code == 204
    assert not (settings.ocr_output_root / document.id).exists()
    assert not (settings.mineru_output_root / document.id).exists()


@pytest.mark.anyio
async def test_upload_and_read_document_status(client, db_session) -> None:
    response = await client.post(
        "/documents/upload",
        files={"file": ("lesson.pdf", b"%PDF-1.4 test", "application/pdf")},
    )

    assert response.status_code == 201
    payload = response.json()
    document = payload["document"]
    document_id = document["id"]
    assert document["filename"] == "lesson.pdf"
    assert document["file_type"] == "pdf"
    assert document["status"] == "uploaded"
    assert payload["job"]["status"] == "queued"

    status_response = await client.get(f"/documents/{document_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["latest_job"]["current_step"] == "queued"

    assert (await client.get(f"/documents/{document_id}/pages")).json() == []
    assert (await client.get(f"/documents/{document_id}/blocks")).json() == []

    list_response = await client.get("/documents")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [document_id]

    stored_path = Path(document["storage_url"])
    assert stored_path.exists()

    assert (await client.delete(f"/documents/{document_id}")).status_code == 409
    db_session.get(Document, document_id).status = "parsed"
    db_session.commit()
    output_dir = get_settings().mineru_output_root / document_id
    output_dir.mkdir(parents=True)
    (output_dir / "result.json").write_text("{}", encoding="utf-8")
    delete_response = await client.delete(f"/documents/{document_id}")
    assert delete_response.status_code == 204
    assert not stored_path.parent.exists()
    assert not output_dir.exists()
    assert (await client.get(f"/documents/{document_id}")).status_code == 404
    assert (await client.get("/documents")).json() == []


@pytest.mark.anyio
async def test_rejects_unsupported_upload_without_creating_storage(client) -> None:
    response = await client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"plain text", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
    assert not get_settings().upload_root.exists()


@pytest.mark.anyio
async def test_upload_cleans_storage_when_database_commit_fails(
    client, db_session, monkeypatch
) -> None:
    def fail_commit() -> None:
        raise RuntimeError("forced database failure")

    monkeypatch.setattr(db_session, "commit", fail_commit)

    response = await client.post(
        "/documents/upload",
        files={"file": ("lesson.pdf", b"%PDF-1.4 test", "application/pdf")},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Could not persist the uploaded document."
    upload_root = get_settings().upload_root
    assert upload_root.exists()
    assert list(upload_root.iterdir()) == []


@pytest.mark.anyio
async def test_unknown_document_returns_not_found(client) -> None:
    response = await client.get("/documents/missing/status")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


@pytest.mark.anyio
async def test_retry_preserves_original_and_rejects_duplicate(client, db_session) -> None:
    uploaded = await client.post(
        "/documents/upload",
        files={"file": ("lesson.pdf", b"%PDF-1.4 test", "application/pdf")},
    )
    document_id = uploaded.json()["document"]["id"]
    document = db_session.get(Document, document_id)
    document.status = "failed"
    db_session.commit()
    assert (await client.get(f"/documents/{document_id}/file")).status_code == 200
    retried = await client.post(f"/documents/{document_id}/retry")
    assert retried.status_code == 200
    assert retried.json()["status"] == "uploaded"
    assert retried.json()["latest_job"]["status"] == "queued"
    assert (await client.post(f"/documents/{document_id}/retry")).status_code == 409


@pytest.mark.anyio
async def test_document_file_is_served_inline(client) -> None:
    response = await client.post(
        "/documents/upload",
        files={"file": ("lesson.pdf", b"%PDF-1.4 test", "application/pdf")},
    )
    document_id = response.json()["document"]["id"]

    file_response = await client.get(f"/documents/{document_id}/file")

    assert file_response.status_code == 200
    assert file_response.headers["content-type"] == "application/pdf"
    assert file_response.headers["content-disposition"].startswith("inline;")
    assert file_response.content == b"%PDF-1.4 test"


@pytest.mark.anyio
async def test_document_preview_is_empty_before_parser_output(client) -> None:
    response = await client.post(
        "/documents/upload",
        files={"file": ("lesson.pdf", b"%PDF-1.4 test", "application/pdf")},
    )
    document_id = response.json()["document"]["id"]

    preview_response = await client.get(f"/documents/{document_id}/preview")

    assert preview_response.status_code == 200
    assert preview_response.json()["document"]["id"] == document_id
    assert preview_response.json()["pages"] == []
    assert preview_response.json()["blocks"] == []


@pytest.mark.anyio
async def test_document_preview_normalizes_latest_mineru_output(
    client, db_session
) -> None:
    response = await client.post(
        "/documents/upload",
        files={"file": ("lesson.pdf", b"%PDF-1.4 test", "application/pdf")},
    )
    document_id = response.json()["document"]["id"]
    db_session.add(
        OCROutput(
            document_id=document_id,
            engine="mineru",
            raw_output={
                "pages": [
                    {
                        "page_idx": 0,
                        "blocks": [
                            {
                                "type": "text",
                                "index": 0,
                                "bbox": [0.1, 0.2, 0.8, 0.4],
                                "content": [{"type": "text", "content": "Bài học"}],
                            }
                        ],
                    }
                ]
            },
            markdown_output="Bài học",
        )
    )
    db_session.commit()

    preview_response = await client.get(f"/documents/{document_id}/preview")
    preview = preview_response.json()

    assert preview_response.status_code == 200
    assert preview["source_engine"] == "mineru"
    assert preview["pages"][0]["page_number"] == 1
    assert preview["blocks"][0]["text"] == "Bài học"
    assert preview["blocks"][0]["coordinate_system"] == "normalized_0_1"
