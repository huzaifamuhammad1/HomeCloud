from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import mimetypes
import shutil

from .database import sha256_file


def extension_of(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def build_stored_name(filename: str) -> str:
    ext = extension_of(filename)
    suffix = f".{ext}" if ext else ""
    return f"{uuid4().hex}{suffix}"


def category_for_extension(ext: str, image_exts: set[str], video_exts: set[str]) -> str:
    if ext in image_exts:
        return "photos"
    if ext in video_exts:
        return "videos"
    return "files"


def save_upload(file_storage, storage_root: Path, image_exts: set[str], video_exts: set[str]) -> dict:
    ext = extension_of(file_storage.filename)
    category = category_for_extension(ext, image_exts, video_exts)

    target_dir = Path(storage_root) / category
    target_dir.mkdir(parents=True, exist_ok=True)

    stored_name = build_stored_name(file_storage.filename)
    destination = target_dir / stored_name
    file_storage.save(destination)

    mime_type = (
        file_storage.mimetype
        or mimetypes.guess_type(file_storage.filename)[0]
        or "application/octet-stream"
    )

    return {
        "id": uuid4().hex,
        "original_name": file_storage.filename,
        "stored_name": stored_name,
        "size_bytes": destination.stat().st_size,
        "mime_type": mime_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "relative_path": f"{category}/{stored_name}",
        "checksum_sha256": sha256_file(destination),
        "category": category,
        "source": "upload",
        "_absolute_path": destination,
    }


def resolve_record_path(storage_root: Path, relative_path: str):
    root = Path(storage_root).resolve()
    candidate = (root / relative_path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError:
        return None

    return candidate


def storage_summary(storage_root: Path, indexed_bytes: int, indexed_count: int):
    root = Path(storage_root)
    root.mkdir(parents=True, exist_ok=True)
    disk = shutil.disk_usage(root)

    return {
        "homecloud_used_bytes": indexed_bytes,
        "disk_total_bytes": disk.total,
        "disk_free_bytes": disk.free,
        "item_count": indexed_count,
    }
