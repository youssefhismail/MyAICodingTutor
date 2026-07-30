"""Documents API routes."""

from fastapi import APIRouter, HTTPException

from backend.database.supabase import get_documents_by_session
from backend.models.responses import DocumentResponse
from backend.services.upload_service import remove_document


router = APIRouter(tags=["documents"])


@router.get("/sessions/{session_id}/documents", response_model=list[DocumentResponse])
def get_session_documents(session_id: str) -> list[DocumentResponse]:
    """Return all documents for one session."""
    try:
        documents = get_documents_by_session(session_id)
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return [
        DocumentResponse(
            document_id=doc.document_id,
            filename=doc.filename,
        )
        for doc in documents
    ]


@router.delete("/documents/{document_id}")
def delete_document(document_id: str) -> dict[str, str]:
    """Delete a specific document."""
    try:
        remove_document(document_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return {"status": "deleted"}
