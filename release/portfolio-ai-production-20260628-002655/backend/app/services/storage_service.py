"""Local filesystem storage for uploaded resumes and generated exports.

Isolated behind this module so swapping to S3/GCS later means changing
one file, not every route that touches a file path.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


class UnsupportedFileTypeError(Exception):
    pass


class FileTooLargeError(Exception):
    def __init__(self, size_bytes: int, max_bytes: int) -> None:
        self.size_bytes = size_bytes
        self.max_bytes = max_bytes
        super().__init__(f"File is {size_bytes} bytes, which exceeds the {max_bytes} byte limit")


_PDF_MAGIC_BYTES = b"%PDF-"


def validate_upload(file: UploadFile, *, content: bytes) -> None:
    if file.content_type not in settings.ALLOWED_UPLOAD_CONTENT_TYPES:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{file.content_type}'. Only PDF files are accepted."
        )
    if not content.startswith(_PDF_MAGIC_BYTES):
        # The browser-reported Content-Type is client-controlled and easy to spoof,
        # so it's only a first filter — the actual file signature is the real check.
        raise UnsupportedFileTypeError("This file isn't a valid PDF. Only PDF files are accepted.")
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise FileTooLargeError(len(content), settings.MAX_UPLOAD_SIZE_BYTES)


def save_resume_pdf(content: bytes, *, user_id: str) -> Path:
    """Persist an uploaded resume PDF under a per-user, content-addressed
    path and return the absolute path written.
    """
    user_dir = settings.RESUME_STORAGE_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    dest = user_dir / f"{uuid.uuid4()}.pdf"
    dest.write_bytes(content)
    return dest
