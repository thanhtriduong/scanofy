from pathlib import Path

import pytest

from app.core.config import get_settings


@pytest.mark.anyio
async def test_upload_and_read_document_status(client) -> None:
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

    delete_response = await client.delete(f"/documents/{document_id}")
    assert delete_response.status_code == 204
    assert not stored_path.parent.exists()


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
