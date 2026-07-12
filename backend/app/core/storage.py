import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


class StorageService:
    """
    Abstraction over file storage. Today this writes to local disk.
    Later (deployment), we can swap the internals for an S3/R2-compatible
    client without changing any calling code, because callers only ever
    interact with save_file() and get_full_path().
    """

    def __init__(self):
        self.base_dir = Path(settings.STORAGE_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _validate(self, file: UploadFile) -> str:
        extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '.{extension}'. "
                f"Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            )
        return extension

    def save_file(self, file: UploadFile) -> tuple[str, str]:
        """
        Saves the uploaded file to disk with a unique name (prevents
        collisions/overwrites) and returns (storage_path, extension).
        """
        extension = self._validate(file)

        unique_name = f"{uuid.uuid4()}.{extension}"
        destination = self.base_dir / unique_name

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        size = 0

        # Stream to disk in chunks instead of reading the whole file into
        # memory at once - important once users upload large PDFs/decks.
        with open(destination, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    buffer.close()
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds max size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                    )
                buffer.write(chunk)

        return str(destination), extension

    def get_full_path(self, storage_path: str) -> Path:
        return Path(storage_path)


storage_service = StorageService()