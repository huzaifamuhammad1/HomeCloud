from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Config:
    STORAGE_ROOT = PROJECT_ROOT / "HomeCloudStorage"
    DATA_ROOT = PROJECT_ROOT / "HomeCloudData"
    DATABASE_PATH = DATA_ROOT / "homecloud.db"

    MAX_CONTENT_LENGTH = 500 * 1024 * 1024

    ALLOWED_EXTENSIONS = {
        "jpg", "jpeg", "png", "webp", "heic", "heif", "gif",
        "mp4", "mov", "m4v", "webm",
        "pdf", "txt", "md", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        "csv", "zip",
    }

    IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "heic", "heif", "gif"}
    VIDEO_EXTENSIONS = {"mp4", "mov", "m4v", "webm"}

    PAIRING_TTL_SECONDS = 300
    DEVICE_COOKIE_NAME = "homecloud_device_token"
