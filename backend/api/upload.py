"""Upload API routes."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.models.responses import UploadResponse
from backend.services.upload_service import process_upload


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_document(
    session_id: str = Form(..., description="Current conversation session ID"),
    file: UploadFile = File(..., description="The file to upload"),
) -> UploadResponse:
    """Accept a file upload, validate it, and persist it to Supabase."""
    try:
        result = await process_upload(session_id=session_id, file=file)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return UploadResponse(**result)
