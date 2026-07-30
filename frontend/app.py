"""Streamlit frontend for the AI file assistant."""

from uuid import uuid4

import streamlit as st

from frontend.api.backend_client import (
    delete_session,
    load_conversation_summaries,
    load_session_messages,
    submit_question,
    upload_file,
)
from frontend.ui.render_service import render_chat
from frontend.ui.sidebar_service import render_sidebar


def initialise_session() -> None:
    """Initialise Streamlit session state."""

    st.session_state.setdefault("session_id", str(uuid4()))
    st.session_state.setdefault("filename", "")
    st.session_state.setdefault("document_id", "")
    st.session_state.setdefault("messages", None)
    st.session_state.setdefault("session_contexts", {})
    st.session_state.setdefault("uploader_key", 0)

    if st.session_state.messages is None:
        try:
            st.session_state.messages = load_session_messages(
                st.session_state.session_id
            )
        except RuntimeError:
            st.session_state.messages = []

    restore_session_assets(st.session_state.session_id)


def cache_active_session_assets() -> None:
    """Cache the upload metadata for the active session."""

    if st.session_state.filename:
        st.session_state.session_contexts[st.session_state.session_id] = {
            "filename": st.session_state.filename,
            "document_id": st.session_state.document_id,
        }


def restore_session_assets(session_id: str) -> None:
    """Restore cached upload metadata for a session."""

    cached = st.session_state.session_contexts.get(session_id)

    if cached:
        st.session_state.filename = cached.get("filename", "")
        st.session_state.document_id = cached.get("document_id", "")


def start_new_chat() -> None:
    """Start a brand-new conversation."""

    cache_active_session_assets()

    st.session_state.session_id = str(uuid4())
    st.session_state.filename = ""
    st.session_state.document_id = ""
    st.session_state.messages = []
    st.session_state.uploader_key += 1


def open_conversation(session_id: str) -> None:
    """Load an existing conversation."""

    cache_active_session_assets()

    st.session_state.session_id = session_id

    try:
        st.session_state.messages = load_session_messages(session_id)
    except RuntimeError:
        st.session_state.messages = []

    st.session_state.filename = ""
    st.session_state.document_id = ""
    st.session_state.uploader_key += 1

    restore_session_assets(session_id)

    if (
        not st.session_state.filename
        and st.session_state.messages
    ):
        st.session_state.filename = (
            st.session_state.messages[0].get("filename", "")
        )


def upload_section() -> None:
    """Render the upload widget."""

    st.subheader("📂 Upload File")

    uploaded_file = st.file_uploader(
        "Upload a file",
        type=[
            "py",
            "js",
            "ts",
            "java",
            "cpp",
            "c",
            "cs",
            "go",
            "rs",
            "php",
            "rb",
            "swift",
            "kt",
            "txt",
            "md",
        ],
        label_visibility="collapsed",
        key=f"file_uploader_{st.session_state.uploader_key}",
    )

    if uploaded_file is None:
        return

    try:
        result = upload_file(
            session_id=st.session_state.session_id,
            uploaded_file=uploaded_file,
        )
        st.session_state.filename = uploaded_file.name
        st.session_state.document_id = result.get("document_id", "")
        cache_active_session_assets()
        st.success(f"✅ {result.get('message', 'Upload successful')}")
    except RuntimeError as error:
        st.session_state.filename = ""
        st.session_state.document_id = ""
        st.error(str(error))


def clear_conversation() -> None:
    """Delete the active conversation."""

    if not st.button("🗑️ Clear Conversation"):
        return

    try:
        delete_session(st.session_state.session_id)
        st.session_state.messages = []
        st.rerun()
    except RuntimeError as error:
        st.error(str(error))


def chat_section() -> None:
    """Render the chat interface."""

    st.subheader("Chat")

    with st.form("chat_form", clear_on_submit=True):
        question = st.text_input(
            "You",
            placeholder="Ask a question about the uploaded file",
        )

        send = st.form_submit_button("Send")

    if not send:
        return

    try:
        with st.spinner("Thinking..."):
            message = submit_question(
                session_id=st.session_state.session_id,
                question=question,
            )

        st.session_state.messages.append(message)

    except ValueError as error:
        st.error(str(error))

    except RuntimeError as error:
        st.error(str(error))


def main() -> None:
    """Application entrypoint."""

    initialise_session()

    try:
        conversations = load_conversation_summaries()
    except RuntimeError:
        conversations = []

    render_sidebar(
        conversations=conversations,
        current_session_id=st.session_state.session_id,
        on_new_chat=start_new_chat,
        on_open_conversation=open_conversation,
    )

    upload_section()

    chat_section()

    clear_conversation()

    render_chat(st.session_state.messages)


if __name__ == "__main__":
    main()