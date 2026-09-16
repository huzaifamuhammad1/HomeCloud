from io import BytesIO

import pytest

from homecloud import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app()

    storage = tmp_path / "storage"
    data = tmp_path / "data"

    app.config.update(
        TESTING=True,
        STORAGE_ROOT=storage,
        DATA_ROOT=data,
        DATABASE_PATH=data / "homecloud.db",
    )

    # Re-create the test database using test paths.
    from homecloud.database import init_db
    init_db(app.config["DATABASE_PATH"])

    return app.test_client()


def upload(client, name="family-photo.jpg", body=b"hello-homecloud"):
    return client.post(
        "/upload",
        data={"file": (BytesIO(body), name)},
        content_type="multipart/form-data",
    )


def test_upload_keeps_original_name_and_metadata(client):
    response = upload(client)
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["file"]["original_name"] == "family-photo.jpg"
    assert len(payload["file"]["checksum_sha256"]) == 64


def test_list_uses_database_records(client):
    upload(client)
    listed = client.get("/files").get_json()

    assert listed["ok"] is True
    assert len(listed["items"]) == 1
    assert listed["items"][0]["original_name"] == "family-photo.jpg"


def test_download_uses_original_filename(client):
    payload = upload(client).get_json()
    file_id = payload["file"]["id"]

    response = client.get(f"/download/{file_id}")

    assert response.status_code == 200
    assert response.data == b"hello-homecloud"
    assert "family-photo.jpg" in response.headers["Content-Disposition"]


def test_delete_removes_record_and_file(client):
    payload = upload(client).get_json()
    file_id = payload["file"]["id"]

    deleted = client.delete(f"/files/{file_id}")
    assert deleted.status_code == 200

    listed = client.get("/files").get_json()
    assert listed["items"] == []
