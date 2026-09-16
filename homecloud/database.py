from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import hashlib
import mimetypes
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    original_name TEXT NOT NULL,
    stored_name TEXT NOT NULL UNIQUE,
    size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
    mime_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    relative_path TEXT NOT NULL UNIQUE,
    checksum_sha256 TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('photos', 'videos', 'files')),
    source TEXT NOT NULL DEFAULT 'upload'
);

CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_files_category ON files(category);

CREATE TABLE IF NOT EXISTS pairing_codes (
    id TEXT PRIMARY KEY,
    secret_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_pairing_codes_expires_at
ON pairing_codes(expires_at);

CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    revoked_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_devices_token_hash
ON devices(token_hash);
"""


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def connect(db_path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def init_db(db_path):
    with connect(db_path) as db:
        db.executescript(SCHEMA)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def insert_file(db_path, record: dict):
    with connect(db_path) as db:
        db.execute(
            """
            INSERT INTO files (
                id, original_name, stored_name, size_bytes, mime_type,
                created_at, relative_path, checksum_sha256, category, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["original_name"],
                record["stored_name"],
                int(record["size_bytes"]),
                record["mime_type"],
                record["created_at"],
                record["relative_path"],
                record["checksum_sha256"],
                record["category"],
                record.get("source", "upload"),
            ),
        )


def get_file(db_path, file_id: str):
    with connect(db_path) as db:
        row = db.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    return dict(row) if row else None


def get_file_by_relative_path(db_path, relative_path: str):
    with connect(db_path) as db:
        row = db.execute(
            "SELECT * FROM files WHERE relative_path = ?",
            (relative_path,),
        ).fetchone()
    return dict(row) if row else None


def list_files(db_path):
    with connect(db_path) as db:
        rows = db.execute(
            """
            SELECT *
            FROM files
            ORDER BY datetime(created_at) DESC, rowid DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def delete_file(db_path, file_id: str):
    with connect(db_path) as db:
        db.execute("DELETE FROM files WHERE id = ?", (file_id,))


def total_indexed_bytes(db_path) -> int:
    with connect(db_path) as db:
        row = db.execute(
            "SELECT COALESCE(SUM(size_bytes), 0) AS total FROM files"
        ).fetchone()
    return int(row["total"])


def indexed_count(db_path) -> int:
    with connect(db_path) as db:
        row = db.execute("SELECT COUNT(*) AS count FROM files").fetchone()
    return int(row["count"])


def import_existing_files(db_path, storage_root: Path):
    storage_root = Path(storage_root)

    for category in ("photos", "videos", "files"):
        folder = storage_root / category
        folder.mkdir(parents=True, exist_ok=True)

        for path in folder.iterdir():
            if not path.is_file() or path.name.startswith("."):
                continue

            relative_path = f"{category}/{path.name}"
            if get_file_by_relative_path(db_path, relative_path):
                continue

            stat = path.stat()
            created_at = datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat()

            record = {
                "id": uuid4().hex,
                "original_name": path.name,
                "stored_name": path.name,
                "size_bytes": stat.st_size,
                "mime_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                "created_at": created_at,
                "relative_path": relative_path,
                "checksum_sha256": sha256_file(path),
                "category": category,
                "source": "imported",
            }
            insert_file(db_path, record)


def create_pairing_code(db_path, pairing_id: str, secret_hash: str, created_at: str, expires_at: str):
    with connect(db_path) as db:
        db.execute(
            """
            INSERT INTO pairing_codes (id, secret_hash, created_at, expires_at, used_at)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (pairing_id, secret_hash, created_at, expires_at),
        )


def get_pairing_code_by_hash(db_path, secret_hash: str):
    with connect(db_path) as db:
        row = db.execute(
            "SELECT * FROM pairing_codes WHERE secret_hash = ?",
            (secret_hash,),
        ).fetchone()
    return dict(row) if row else None


def get_pairing_code(db_path, pairing_id: str):
    with connect(db_path) as db:
        row = db.execute(
            "SELECT * FROM pairing_codes WHERE id = ?",
            (pairing_id,),
        ).fetchone()
    return dict(row) if row else None


def mark_pairing_code_used(db_path, pairing_id: str, used_at: str):
    with connect(db_path) as db:
        db.execute(
            """
            UPDATE pairing_codes
            SET used_at = ?
            WHERE id = ? AND used_at IS NULL
            """,
            (used_at, pairing_id),
        )


def cleanup_pairing_codes(db_path, now_iso: str):
    with connect(db_path) as db:
        db.execute(
            """
            DELETE FROM pairing_codes
            WHERE expires_at < ? OR used_at IS NOT NULL
            """,
            (now_iso,),
        )


def create_device(db_path, device_id: str, name: str, token_hash: str, created_at: str):
    with connect(db_path) as db:
        db.execute(
            """
            INSERT INTO devices (
                id, name, token_hash, created_at, last_seen_at, revoked_at
            )
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (device_id, name, token_hash, created_at, created_at),
        )


def get_active_device_by_token_hash(db_path, token_hash: str):
    with connect(db_path) as db:
        row = db.execute(
            """
            SELECT id, name, created_at, last_seen_at, revoked_at
            FROM devices
            WHERE token_hash = ? AND revoked_at IS NULL
            """,
            (token_hash,),
        ).fetchone()
    return dict(row) if row else None


def touch_device(db_path, device_id: str, seen_at: str):
    with connect(db_path) as db:
        db.execute(
            "UPDATE devices SET last_seen_at = ? WHERE id = ? AND revoked_at IS NULL",
            (seen_at, device_id),
        )


def list_devices(db_path):
    with connect(db_path) as db:
        rows = db.execute(
            """
            SELECT id, name, created_at, last_seen_at, revoked_at
            FROM devices
            ORDER BY datetime(created_at) DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def revoke_device(db_path, device_id: str, revoked_at: str):
    with connect(db_path) as db:
        db.execute(
            """
            UPDATE devices
            SET revoked_at = ?
            WHERE id = ? AND revoked_at IS NULL
            """,
            (revoked_at, device_id),
        )
