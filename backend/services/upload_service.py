"""Upload service — validate, read, and persist uploaded documents."""

import json
from pathlib import PurePath

from fastapi import UploadFile

from backend.config import MAX_UPLOAD_SIZE
from backend.database.supabase import (
    delete_document,
    insert_document,
    insert_document_chunks,
)
from backend.services.chunk_service import chunk_document
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
    ".yaml",
    ".json",
    ".sh",
    ".sql",
    ".html",
    ".css",
    ".scss",
    ".sass",
    ".xml",
    ".csv",
    ".pyi",
    ".ipynb",
}


def parse_ipynb(raw_content: str) -> str:
    """Parse a Jupyter Notebook and extract only code and markdown cells."""
    try:
        notebook = json.loads(raw_content)
        extracted_text = []
        for cell in notebook.get("cells", []):
            cell_type = cell.get("cell_type")
            if cell_type in ("code", "markdown"):
                source = cell.get("source", [])
                if isinstance(source, list):
                    source = "".join(source)
                if source:
                    extracted_text.append(f"### {cell_type.capitalize()} Cell ###\n{source}")
        return "\n\n".join(extracted_text)
    except Exception as error:
        raise ValueError("The uploaded file is not a valid Jupyter Notebook.") from error


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

    if filename.lower().endswith(".ipynb"):
        content = parse_ipynb(content)

    # 1. Chunk document in pure Python (no DB writes yet)
    chunks = chunk_document(content)

    # 2. Insert document to get the document_id
    row = insert_document(session_id, filename, content)
    document_id = str(row.get("id", ""))

    # 3. Insert chunks explicitly. Rollback document on failure.
    try:
        insert_document_chunks(document_id, chunks)
    except Exception:
        delete_document(document_id)
        raise

    return {
        "document_id": document_id,
        "filename": filename,
        "message": "Upload successful",
    }


def remove_document(document_id: str) -> None:
    """Remove a document from the session."""
    document_id = require_text(document_id, "Document ID")
    delete_document(document_id)
