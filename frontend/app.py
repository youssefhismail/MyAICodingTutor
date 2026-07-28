"""Streamlit frontend for the AI file assistant."""

from uuid import uuid4

import streamlit as st

from frontend.api.backend_client import (
    delete_session,
    load_conversation_summaries,
    load_session_messages,
    submit_question,
)
from frontend import config as frontend_config
from frontend.services.file_service import load_file
from frontend.ui.render_service import render_chat
from frontend.ui.sidebar_service import render_sidebar


DEFAULT_SYSTEM_PROMPT = getattr(
    frontend_config,
    "DEFAULT_SYSTEM_PROMPT",
    """
You are an expert programming assistant.

Use the uploaded file as the primary source of truth.

If the question cannot be answered from the uploaded file, say that the information is unavailable instead of inventing an answer.

Do not make assumptions beyond what appears in the uploaded file.

If the user asks about previous messages in the current conversation, answer using the conversation history.

If the answer cannot be found in either the uploaded file or the conversation history, clearly say so instead of making something up.
""".strip(),
)


def initialise_session() -> None:
    """Initialise Streamlit session state."""

    st.session_state.setdefault("session_id", str(uuid4()))
    st.session_state.setdefault("context", "")
    st.session_state.setdefault("filename", "")
    st.session_state.setdefault("system_prompt", DEFAULT_SYSTEM_PROMPT)
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
    """Cache the uploaded file for the active session."""

    if st.session_state.context:
        st.session_state.session_contexts[st.session_state.session_id] = {
            "context": st.session_state.context,
            "filename": st.session_state.filename,
        }


def restore_session_assets(session_id: str) -> None:
    """Restore cached file information for a session."""

    cached = st.session_state.session_contexts.get(session_id)

    if cached:
        st.session_state.context = cached.get("context", "")
        st.session_state.filename = cached.get("filename", "")


def start_new_chat() -> None:
    """Start a brand-new conversation."""

    cache_active_session_assets()

    st.session_state.session_id = str(uuid4())
    st.session_state.context = ""
    st.session_state.filename = ""
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

    st.session_state.context = ""
    st.session_state.filename = ""
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
            "md",
            "txt",
            "json",
            "html",
            "css",
            "ipynb",
        ],
        label_visibility="collapsed",
        key=f"file_uploader_{st.session_state.uploader_key}",
    )

    if uploaded_file is None:
        return

    try:
        st.session_state.context = load_file(uploaded_file)
        st.session_state.filename = uploaded_file.name
        cache_active_session_assets()
    except ValueError as error:
        st.session_state.context = ""
        st.session_state.filename = ""
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
                filename=st.session_state.filename,
                system_prompt=st.session_state.system_prompt,
                context=st.session_state.context,
                chat_history=st.session_state.messages,
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