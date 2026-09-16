from pathlib import Path
import os

from flask import Blueprint, current_app, jsonify, render_template, request, send_file

from .database import (
    delete_file,
    get_file,
    get_pairing_code,
    indexed_count,
    insert_file,
    list_devices,
    list_files,
    revoke_device,
    total_indexed_bytes,
    utc_now_iso,
)
from .security import (
    claim_pairing_secret,
    create_pairing_session,
    current_device,
    device_required,
    is_local_admin_request,
    is_tailscale_serve_request,
    local_admin_required,
)
from .storage import (
    extension_of,
    resolve_record_path,
    save_upload,
    storage_summary,
)

main = Blueprint("main", __name__)


def public_record(record: dict):
    return {
        "id": record["id"],
        "original_name": record["original_name"],
        "stored_name": record["stored_name"],
        "size_bytes": record["size_bytes"],
        "mime_type": record["mime_type"],
        "created_at": record["created_at"],
        "relative_path": record["relative_path"],
        "checksum_sha256": record["checksum_sha256"],
        "category": record["category"],
        "source": record["source"],
        "view_url": f"/files/{record['id']}",
        "download_url": f"/download/{record['id']}",
    }


@main.after_app_request
def response_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"

    protected_prefixes = (
        "/api/",
        "/files",
        "/download/",
        "/storage",
        "/upload",
        "/pair",
    )
    if request.path.startswith(protected_prefixes):
        response.headers["Cache-Control"] = "private, no-store"

    return response


@main.get("/")
def index():
    return render_template(
        "index.html",
        local_admin=is_local_admin_request(),
        remote_url=os.environ.get("HOMECLOUD_PUBLIC_URL", ""),
    )


@main.get("/manifest.webmanifest")
def manifest():
    response = current_app.send_static_file("manifest.webmanifest")
    response.headers["Content-Type"] = "application/manifest+json"
    response.headers["Cache-Control"] = "no-cache"
    return response


@main.get("/service-worker.js")
def service_worker():
    response = current_app.send_static_file("service-worker.js")
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


@main.get("/api/status")
def status():
    return jsonify(
        {
            "ok": True,
            "name": "HomeCloud",
            "stage": 6,
            "remote_access": True,
            "https": is_tailscale_serve_request(),
            "message": "HomeCloud is online.",
        }
    )


@main.get("/api/auth/status")
def auth_status():
    device = current_device()

    if not device:
        return jsonify(
            {
                "ok": True,
                "authorized": False,
                "local_admin": False,
            }
        )

    return jsonify(
        {
            "ok": True,
            "authorized": True,
            "local_admin": bool(device.get("local_admin")),
            "device": {
                "id": device["id"],
                "name": device["name"],
            },
        }
    )


@main.get("/pair/setup")
@local_admin_required
def pair_setup():
    try:
        pairing = create_pairing_session()
    except RuntimeError as error:
        return render_template(
            "pair_setup.html",
            error=str(error),
            pairing=None,
        ), 500

    devices = list_devices(current_app.config["DATABASE_PATH"])

    return render_template(
        "pair_setup.html",
        pairing=pairing,
        devices=devices,
        error=None,
    )


@main.get("/api/admin/pairing/<pairing_id>/status")
@local_admin_required
def pairing_status(pairing_id):
    record = get_pairing_code(
        current_app.config["DATABASE_PATH"],
        pairing_id,
    )
    if not record:
        return jsonify({"ok": True, "status": "missing"})
    if record["used_at"]:
        return jsonify({"ok": True, "status": "paired"})
    return jsonify(
        {
            "ok": True,
            "status": "waiting",
            "expires_at": record["expires_at"],
        }
    )


@main.get("/api/admin/devices")
@local_admin_required
def admin_devices():
    return jsonify(
        {
            "ok": True,
            "devices": list_devices(current_app.config["DATABASE_PATH"]),
        }
    )


@main.delete("/api/admin/devices/<device_id>")
@local_admin_required
def admin_revoke_device(device_id):
    revoke_device(
        current_app.config["DATABASE_PATH"],
        device_id,
        utc_now_iso(),
    )
    return jsonify({"ok": True})


@main.get("/pair")
def pair_phone():
    secret = request.args.get("secret", "")
    return render_template("pair_phone.html", secret=secret)


@main.post("/api/pair/claim")
def pair_claim():
    payload = request.get_json(silent=True) or {}
    secret = payload.get("secret", "")
    device_name = payload.get("device_name", "iPhone")

    result, error = claim_pairing_secret(secret, device_name)
    if error:
        return jsonify({"ok": False, "error": error}), 400

    response = jsonify(
        {
            "ok": True,
            "device": {
                "id": result["device_id"],
                "name": result["device_name"],
            },
        }
    )

    response.set_cookie(
        current_app.config["DEVICE_COOKIE_NAME"],
        result["token"],
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        secure=True,
        samesite="Strict",
        path="/",
    )
    return response


@main.post("/api/auth/forget-this-device")
def forget_this_device():
    response = jsonify({"ok": True})
    response.delete_cookie(
        current_app.config["DEVICE_COOKIE_NAME"],
        path="/",
        secure=True,
        samesite="Strict",
    )
    return response


@main.get("/files")
@device_required
def files():
    records = [
        public_record(record)
        for record in list_files(current_app.config["DATABASE_PATH"])
    ]
    return jsonify({"ok": True, "items": records})


@main.get("/files/<file_id>")
@device_required
def view_file(file_id):
    record = get_file(current_app.config["DATABASE_PATH"], file_id)
    if not record:
        return jsonify({"ok": False, "error": "File not found."}), 404

    path = resolve_record_path(
        current_app.config["STORAGE_ROOT"],
        record["relative_path"],
    )
    if not path or not path.is_file():
        return jsonify({"ok": False, "error": "The file is missing from disk."}), 404

    return send_file(path, as_attachment=False, conditional=True)


@main.get("/download/<file_id>")
@device_required
def download_file(file_id):
    record = get_file(current_app.config["DATABASE_PATH"], file_id)
    if not record:
        return jsonify({"ok": False, "error": "File not found."}), 404

    path = resolve_record_path(
        current_app.config["STORAGE_ROOT"],
        record["relative_path"],
    )
    if not path or not path.is_file():
        return jsonify({"ok": False, "error": "The file is missing from disk."}), 404

    return send_file(
        path,
        as_attachment=True,
        download_name=record["original_name"],
        conditional=True,
    )


@main.delete("/files/<file_id>")
@device_required
def remove_file(file_id):
    record = get_file(current_app.config["DATABASE_PATH"], file_id)
    if not record:
        return jsonify({"ok": False, "error": "File not found."}), 404

    path = resolve_record_path(
        current_app.config["STORAGE_ROOT"],
        record["relative_path"],
    )
    if path and path.exists():
        path.unlink()

    delete_file(current_app.config["DATABASE_PATH"], file_id)
    return jsonify({"ok": True})


@main.get("/storage")
@device_required
def storage():
    indexed_bytes = total_indexed_bytes(current_app.config["DATABASE_PATH"])
    count = indexed_count(current_app.config["DATABASE_PATH"])

    return jsonify(
        {
            "ok": True,
            **storage_summary(
                current_app.config["STORAGE_ROOT"],
                indexed_bytes=indexed_bytes,
                indexed_count=count,
            ),
        }
    )


@main.post("/upload")
@device_required
def upload():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No file was selected."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Choose a file first."}), 400

    extension = extension_of(file.filename)
    allowed = current_app.config["ALLOWED_EXTENSIONS"]

    if extension not in allowed:
        readable = ", ".join(sorted(allowed))
        return jsonify(
            {
                "ok": False,
                "error": f"That file type is not allowed yet. Supported: {readable}",
            }
        ), 400

    record = save_upload(
        file,
        current_app.config["STORAGE_ROOT"],
        current_app.config["IMAGE_EXTENSIONS"],
        current_app.config["VIDEO_EXTENSIONS"],
    )

    absolute_path = Path(record.pop("_absolute_path"))
    try:
        insert_file(current_app.config["DATABASE_PATH"], record)
    except Exception:
        if absolute_path.exists():
            absolute_path.unlink()
        raise

    return jsonify({"ok": True, "file": public_record(record)})
