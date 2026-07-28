"""HTTP client helpers used by the Streamlit frontend."""

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


def submit_question(
    session_id: str,
    filename: str,
    system_prompt: str,
    context: str,
    chat_history: list[dict[str, str]],
    question: str,
) -> dict[str, str]:
    response = _request(
        "POST",
        "/chat",
        timeout=120,
        json={
            "session_id": session_id,
            "filename": filename,
            "system_prompt": system_prompt,
            "context": context,
            "chat_history": chat_history,
            "question": question,
        },
    )
    return response.json()
