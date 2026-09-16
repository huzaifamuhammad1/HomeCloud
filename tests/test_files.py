from io import BytesIO

import pytest

from homecloud import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app()
    app.config.update(TESTING=True, STORAGE_ROOT=tmp_path)
    return app.test_client()


def upload(client, name="photo.jpg", body=b"hello"):
    return client.post(
        "/upload",
        data={"file": (BytesIO(body), name)},
        content_type="multipart/form-data",
    )


def test_upload_then_list(client):
    response = upload(client)
    assert response.status_code == 200

    listed = client.get("/files").get_json()
    assert listed["ok"] is True
    assert len(listed["items"]) == 1


def test_download_and_delete(client):
    payload = upload(client).get_json()
    item_id = payload["file"]["stored_name"]

    download = client.get(f"/download/{item_id}")
    assert download.status_code == 200
    assert download.data == b"hello"

    deleted = client.delete(f"/files/{item_id}")
    assert deleted.status_code == 200
    assert deleted.get_json()["ok"] is True

    missing = client.get(f"/files/{item_id}")
    assert missing.status_code == 404


def test_storage_summary(client):
    upload(client, "a.jpg", b"abc")
    storage = client.get("/storage").get_json()
    assert storage["ok"] is True
    assert storage["item_count"] == 1
    assert storage["homecloud_used_bytes"] == 3
