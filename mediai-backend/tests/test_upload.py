"""Tests for POST /upload."""

import io


def test_upload_txt_file_succeeds(client):
    file_content = b"Diabetes is a chronic condition affecting blood sugar regulation."
    files = {"file": ("diabetes.txt", io.BytesIO(file_content), "text/plain")}

    response = client.post("/upload", files=files)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    assert body["document"].startswith("diabetes")
    assert body["document"].endswith(".txt")
    assert body["chunks_stored"] == 3


def test_upload_rejects_unsupported_file_extension(client):
    files = {"file": ("malware.exe", io.BytesIO(b"binary-content"), "application/octet-stream")}

    response = client.post("/upload", files=files)

    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "error"
    assert "format" in body["message"].lower()


def test_upload_rejects_empty_file(client):
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}

    response = client.post("/upload", files=files)

    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "error"
