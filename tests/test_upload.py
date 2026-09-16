from io import BytesIO

import pytest

from homecloud import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app()
    app.config.update(
        TESTING=True,
        STORAGE_ROOT=tmp_path,
    )
    return app.test_client()


def test_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def test_upload_jpeg(client):
    response = client.post(
        "/upload",
        data={"file": (BytesIO(b"fake-jpeg-bytes"), "photo.jpg")},
        content_type="multipart/form-data",
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["file"]["original_name"] == "photo.jpg"


def test_rejects_disallowed_type(client):
    response = client.post(
        "/upload",
        data={"file": (BytesIO(b"not-allowed"), "malware.exe")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.get_json()["ok"] is False
