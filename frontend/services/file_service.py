"""Read and validate an uploaded text file."""

from frontend.config import MAX_FILE_SIZE


def validate_file(uploaded_file) -> None:
    """Raise ValueError when an upload cannot be used as file context."""
    if uploaded_file is None:
        raise ValueError("Choose a file to upload.")
    if uploaded_file.size == 0:
        raise ValueError("The uploaded file is empty.")
    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValueError(
            f"The uploaded file is too large. Maximum size is {MAX_FILE_SIZE / 1024:g} KB."
        )


def read_file(uploaded_file) -> str:
    """Return the complete UTF-8 text from a Streamlit UploadedFile."""
    uploaded_file.seek(0)
    try:
        return uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("Upload a UTF-8 text file.") from error


def load_file(uploaded_file) -> str:
    """Validate an upload, then read all of its text into memory."""
    validate_file(uploaded_file)
    return read_file(uploaded_file)
