from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import wraps
from uuid import uuid4
import base64
import io
import os
import secrets

import qrcode
from flask import current_app, jsonify, request

from .database import (
    cleanup_pairing_codes,
    create_device,
    create_pairing_code,
    get_active_device_by_token_hash,
    get_pairing_code_by_hash,
    mark_pairing_code_used,
    sha256_text,
    touch_device,
    utc_now_iso,
)


TAILSCALE_IDENTITY_HEADER = "Tailscale-User-Login"


def is_tailscale_serve_request() -> bool:
    # Tailscale Serve strips user-supplied identity headers and adds its own.
    # The backend listens only on localhost, so this header is trusted here.
    return bool(request.headers.get(TAILSCALE_IDENTITY_HEADER))


def is_local_admin_request() -> bool:
    # Direct browser request on the Mac itself.
    # Requests proxied by Tailscale Serve also arrive from loopback, so the
    # identity header is what prevents remote Serve traffic from becoming admin.
    return (
        request.remote_addr in {"127.0.0.1", "::1"}
        and not is_tailscale_serve_request()
    )


def local_admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_local_admin_request():
            return jsonify(
                {
                    "ok": False,
                    "error": "This admin action can only be opened directly on the Mac.",
                }
            ), 403
        return view(*args, **kwargs)

    return wrapped


def current_device():
    if is_local_admin_request():
        return {
            "id": "local-mac",
            "name": "This Mac",
            "local_admin": True,
        }

    token = request.cookies.get(current_app.config["DEVICE_COOKIE_NAME"])
    if not token:
        return None

    token_hash = sha256_text(token)
    device = get_active_device_by_token_hash(
        current_app.config["DATABASE_PATH"],
        token_hash,
    )
    if not device:
        return None

    touch_device(
        current_app.config["DATABASE_PATH"],
        device["id"],
        utc_now_iso(),
    )
    device["local_admin"] = False
    return device


def device_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        device = current_device()
        if not device:
            return jsonify(
                {
                    "ok": False,
                    "error": "This device is not paired with HomeCloud.",
                    "code": "PAIRING_REQUIRED",
                }
            ), 401
        return view(*args, **kwargs)

    return wrapped


def create_pairing_session():
    db_path = current_app.config["DATABASE_PATH"]
    cleanup_pairing_codes(db_path, utc_now_iso())

    public_url = os.environ.get("HOMECLOUD_PUBLIC_URL", "").strip().rstrip("/")
    if not public_url.startswith("https://"):
        raise RuntimeError(
            "Secure remote URL is not configured. Run 04_SETUP_REMOTE_ACCESS.command first."
        )

    pairing_id = uuid4().hex
    secret = secrets.token_urlsafe(32)

    created = datetime.now(timezone.utc)
    expires = created + timedelta(
        seconds=current_app.config["PAIRING_TTL_SECONDS"]
    )

    create_pairing_code(
        db_path=db_path,
        pairing_id=pairing_id,
        secret_hash=sha256_text(secret),
        created_at=created.isoformat(),
        expires_at=expires.isoformat(),
    )

    pair_url = f"{public_url}/pair?secret={secret}"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=9,
        border=4,
    )
    qr.add_data(pair_url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    qr_data_url = "data:image/png;base64," + base64.b64encode(
        buffer.getvalue()
    ).decode("ascii")

    return {
        "pairing_id": pairing_id,
        "pair_url": pair_url,
        "qr_data_url": qr_data_url,
        "expires_at": expires.isoformat(),
        "public_url": public_url,
    }


def claim_pairing_secret(secret: str, device_name: str):
    if not secret:
        return None, "The pairing code is missing."

    db_path = current_app.config["DATABASE_PATH"]
    record = get_pairing_code_by_hash(db_path, sha256_text(secret))

    if not record:
        return None, "This pairing code is invalid or has already been used."

    if record["used_at"]:
        return None, "This pairing code has already been used."

    expires_at = datetime.fromisoformat(record["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        return None, "This pairing code has expired. Create a new one on your Mac."

    raw_token = secrets.token_urlsafe(48)
    device_id = uuid4().hex
    created_at = utc_now_iso()
    safe_name = (device_name or "Paired phone").strip()[:80] or "Paired phone"

    create_device(
        db_path=db_path,
        device_id=device_id,
        name=safe_name,
        token_hash=sha256_text(raw_token),
        created_at=created_at,
    )
    mark_pairing_code_used(db_path, record["id"], created_at)

    return {
        "device_id": device_id,
        "device_name": safe_name,
        "token": raw_token,
    }, None
