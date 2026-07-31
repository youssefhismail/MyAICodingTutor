"""HTTP client helpers used by the Streamlit frontend."""

import json
import time
from collections.abc import Iterator

import requests

from frontend.config import BACKEND_BASE_URL


def _backend_url(path: str) -> str:
    return f"{BACKEND_BASE_URL.rstrip('/')}{path}"


def _raise_backend_error(response: requests.Response) -> None:
    try:
        payload = response.json()
    except ValueError:
        payload = None

    detail = None
    if isinstance(payload, dict):
        detail = payload.get("detail")

    message = detail if detail is not None else response.text
    raise RuntimeError(message or f"Request failed with status code {response.status_code}.")


def _request(method: str, path: str, *, timeout: int, **kwargs):
    response = requests.request(method, _backend_url(path), timeout=timeout, **kwargs)
    if not response.ok:
        _raise_backend_error(response)
    return response


def load_conversation_summaries() -> list[dict[str, str]]:
    response = _request("GET", "/sessions", timeout=30)
    return response.json()


def load_session_messages(session_id: str) -> list[dict[str, str]]:
    response = _request("GET", f"/sessions/{session_id}", timeout=30)
    return response.json()


def delete_session(session_id: str) -> None:
    _request("DELETE", f"/sessions/{session_id}", timeout=30)


def load_session_documents(session_id: str) -> list[dict[str, str]]:
    response = _request("GET", f"/sessions/{session_id}/documents", timeout=30)
    return response.json()


def delete_document(document_id: str) -> None:
    _request("DELETE", f"/documents/{document_id}", timeout=30)


def submit_question(
    session_id: str,
    question: str,
) -> dict[str, str]:
    response = _request(
        "POST",
        "/chat",
        timeout=120,
        json={
            "session_id": session_id,
            "question": question,
        },
    )
    return response.json()


def stream_question(session_id: str, question: str) -> Iterator[str]:
    """Stream the assistant's answer token-by-token from the backend.

    POSTs to ``POST /chat/stream`` and decodes each Server-Sent Event,
    yielding the text of every ``chunk`` event.  Stops cleanly on ``done``
    and raises ``RuntimeError`` on ``error``.

    Implementation note — why ``response.raw`` instead of ``iter_lines()``:
    ``requests.iter_lines()`` calls ``iter_content(chunk_size=512)`` internally.
    Because SSE tokens are typically 1–15 bytes, the library silently
    accumulates ~30-50 tokens before yielding a line.  Reading from
    ``response.raw`` with ``amt=1`` removes that buffer entirely so every
    token is delivered the instant it arrives over the wire.

    Yields:
        Individual text tokens as they arrive.

    Raises:
        RuntimeError: if the backend returns an error status or an error event.
    """
    response = requests.post(
        _backend_url("/chat/stream"),
        json={"session_id": session_id, "question": question},
        stream=True,
        timeout=120,
    )
    if not response.ok:
        _raise_backend_error(response)

    # Read the raw socket one byte at a time to avoid requests' internal
    # 512-byte iter_lines buffer.  Accumulate bytes into a line buffer and
    # process each complete SSE line as soon as a newline is received.
    raw = response.raw
    raw.decode_content = True  # decompress gzip/deflate if the server sends it
    line_buf: list[bytes] = []

    # [DBG] Client-side timing
    t_client_start = time.perf_counter()
    chunk_count = 0
    print(f"[DBG][stream_question] HTTP connection open, reading raw bytes", flush=True)

    while True:
        byte = raw.read(1)
        if not byte:
            print(
                f"[DBG][stream_question] Raw socket EOF at "
                f"t={(time.perf_counter() - t_client_start):.3f}s",
                flush=True,
            )
            break
        if byte == b"\n":
            line = b"".join(line_buf).decode("utf-8", errors="replace")
            line_buf.clear()

            if not line or not line.startswith("data: "):
                continue

            payload = json.loads(line[len("data: "):])
            event_type = payload.get("type")

            if event_type == "done":
                print(
                    f"[DBG][stream_question] 'done' event received at "
                    f"t={(time.perf_counter() - t_client_start):.3f}s "
                    f"total_chunks={chunk_count}",
                    flush=True,
                )
                return
            if event_type == "error":
                raise RuntimeError(payload.get("message", "Unknown streaming error."))
            if event_type == "chunk":
                text = payload.get("text", "")
                if text:
                    chunk_count += 1
                    now = time.perf_counter()
                    print(
                        f"[DBG][stream_question] chunk #{chunk_count} "
                        f"t={(now - t_client_start):.3f}s "
                        f"len={len(text)} repr={text!r}",
                        flush=True,
                    )
                    yield text
        else:
            line_buf.append(byte)


def upload_file(session_id: str, uploaded_file) -> dict[str, str]:
    """Upload a file to the backend via multipart/form-data."""
    uploaded_file.seek(0)
    response = _request(
        "POST",
        "/upload",
        timeout=60,
        files={"file": (uploaded_file.name, uploaded_file, "application/octet-stream")},
        data={"session_id": session_id},
    )
    return response.json()
