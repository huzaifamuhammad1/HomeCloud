from io import BytesIO
import re

import pytest

from homecloud import create_app
from homecloud.database import create_pairing_code, sha256_text
from homecloud.security import claim_pairing_secret


@pytest.fixture()
def app(tmp_path):
    application = create_app()

    storage = tmp_path / "storage"
    data = tmp_path / "data"

    application.config.update(
        TESTING=True,
        STORAGE_ROOT=storage,
        DATA_ROOT=data,
        DATABASE_PATH=data / "homecloud.db",
    )

    from homecloud.database import init_db
    init_db(application.config["DATABASE_PATH"])

    return application


def test_unpaired_device_cannot_list_files(app):
    client = app.test_client()
    response = client.get("/files", environ_base={"REMOTE_ADDR": "192.168.1.50"})
    assert response.status_code == 401
    assert response.get_json()["code"] == "PAIRING_REQUIRED"


def test_local_mac_can_access_without_device_token(app):
    client = app.test_client()
    response = client.get("/files", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert response.status_code == 200


def test_pairing_claim_sets_cookie_and_allows_access(app):
    secret = "temporary-pairing-secret"

    with app.app_context():
        create_pairing_code(
            app.config["DATABASE_PATH"],
            pairing_id="pair1",
            secret_hash=sha256_text(secret),
            created_at="2099-01-01T00:00:00+00:00",
            expires_at="2099-01-01T00:05:00+00:00",
        )

    client = app.test_client()
    response = client.post(
        "/api/pair/claim",
        json={"secret": secret, "device_name": "Test iPhone"},
        environ_base={"REMOTE_ADDR": "192.168.1.50"},
    )

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    assert "homecloud_device_token=" in response.headers.get("Set-Cookie", "")

    protected = client.get(
        "/files",
        environ_base={"REMOTE_ADDR": "192.168.1.50"},
    )
    assert protected.status_code == 200


def test_pairing_secret_is_single_use(app):
    secret = "one-use-secret"

    with app.app_context():
        create_pairing_code(
            app.config["DATABASE_PATH"],
            pairing_id="pair2",
            secret_hash=sha256_text(secret),
            created_at="2099-01-01T00:00:00+00:00",
            expires_at="2099-01-01T00:05:00+00:00",
        )

    first = app.test_client().post(
        "/api/pair/claim",
        json={"secret": secret, "device_name": "Phone A"},
        environ_base={"REMOTE_ADDR": "192.168.1.50"},
    )
    second = app.test_client().post(
        "/api/pair/claim",
        json={"secret": secret, "device_name": "Phone B"},
        environ_base={"REMOTE_ADDR": "192.168.1.51"},
    )

    assert first.status_code == 200
    assert second.status_code == 400


def test_upload_still_works_for_local_mac(app):
    client = app.test_client()
    response = client.post(
        "/upload",
        data={"file": (BytesIO(b"hello"), "hello.jpg")},
        content_type="multipart/form-data",
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
    )
    assert response.status_code == 200
