"""Upload service — validate, read, and persist uploaded documents."""

from pathlib import PurePath

from fastapi import UploadFile

from backend.config import MAX_UPLOAD_SIZE
from backend.database.supabase import upsert_document
from backend.utils.validators import require_text


ALLOWED_EXTENSIONS: set[str] = {
    ".py",
    ".js",
    ".ts",
    ".java",
    ".cpp",
    ".c",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".txt",
    ".md",
}


def validate_upload(filename: str, size: int) -> None:
    """Raise ValueError when the upload cannot be accepted."""
    if not filename or not filename.strip():
        raise ValueError("No file was provided.")
    if size == 0:
        raise ValueError("The uploaded file is empty.")
    if size > MAX_UPLOAD_SIZE:
        limit_mb = MAX_UPLOAD_SIZE / (1024 * 1024)
        raise ValueError(
            f"The uploaded file exceeds the {limit_mb:g} MB size limit."
        )

    extension = PurePath(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(
            f"Unsupported file type '{extension}'. "
            f"Supported extensions: {supported}"
        )


async def process_upload(session_id: str, file: UploadFile) -> dict[str, str]:
    """
    Orchestrate an upload: validate → read → store.

    Future RAG extension point:
        validate → read → chunk_document → generate_embeddings → store
    The return type and caller contract remain unchanged.
    """
    session_id = require_text(session_id, "Session ID")

    filename = file.filename or ""
    raw_bytes = await file.read()
    size = len(raw_bytes)

    validate_upload(filename, size)

    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("The uploaded file is not valid UTF-8 text.") from error

    # --- future RAG steps would go here ---
    # chunks = chunk_document(content)
    # embeddings = generate_embeddings(chunks)
    # store with embeddings

    row = upsert_document(session_id, filename, content)

    return {
        "document_id": str(row.get("id", "")),
        "filename": filename,
        "message": "Upload successful",
    }
