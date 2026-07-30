"""Streamlit frontend for the AI file assistant."""

from uuid import uuid4

import streamlit as st

from frontend.api.backend_client import (
    delete_session,
    load_conversation_summaries,
    load_session_messages,
    submit_question,
    upload_file,
    load_session_documents,
    delete_document,
)
from frontend.ui.render_service import render_chat
from frontend.ui.sidebar_service import render_sidebar


def initialise_session() -> None:
    """Initialise Streamlit session state."""

    st.session_state.setdefault("session_id", str(uuid4()))
    st.session_state.setdefault("documents", [])
    st.session_state.setdefault("messages", None)
    st.session_state.setdefault("uploader_key", 0)

    if st.session_state.messages is None:
        try:
            st.session_state.messages = load_session_messages(
                st.session_state.session_id
            )
        except RuntimeError:
            st.session_state.messages = []

    if not st.session_state.documents:
        try:
            st.session_state.documents = load_session_documents(
                st.session_state.session_id
            )
        except RuntimeError:
            st.session_state.documents = []





def start_new_chat() -> None:
    """Start a brand-new conversation."""

    st.session_state.session_id = str(uuid4())
    st.session_state.documents = []
    st.session_state.messages = []
    st.session_state.uploader_key += 1


def open_conversation(session_id: str) -> None:
    """Load an existing conversation."""

    st.session_state.session_id = session_id

    try:
        st.session_state.messages = load_session_messages(session_id)
    except RuntimeError:
        st.session_state.messages = []

    try:
        st.session_state.documents = load_session_documents(session_id)
    except RuntimeError:
        st.session_state.documents = []

    st.session_state.uploader_key += 1


def upload_section() -> None:
    """Render the upload widget."""

    st.subheader("📂 Upload Files")

    uploaded_files = st.file_uploader(
        "Upload files",
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
        accept_multiple_files=True,
    )

    if uploaded_files:
        if st.button("Upload Selected Files"):
            for uploaded_file in uploaded_files:
                try:
                    result = upload_file(
                        session_id=st.session_state.session_id,
                        uploaded_file=uploaded_file,
                    )
                    st.session_state.documents.append({
                        "document_id": result.get("document_id", ""),
                        "filename": uploaded_file.name,
                    })
                    st.success(f"✅ {uploaded_file.name} uploaded successfully")
                except RuntimeError as error:
                    st.error(f"Failed to upload {uploaded_file.name}: {str(error)}")
            
            st.session_state.uploader_key += 1
            st.rerun()

    if st.session_state.documents:
        st.markdown("### 📄 Attached Documents")
        for doc in st.session_state.documents:
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.write(doc["filename"])
            with col2:
                if st.button("🗑️", key=f"del_{doc['document_id']}", help="Delete document"):
                    try:
                        delete_document(doc["document_id"])
                        st.session_state.documents = [
                            d for d in st.session_state.documents 
                            if d["document_id"] != doc["document_id"]
                        ]
                        st.rerun()
                    except RuntimeError as error:
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
            placeholder="Ask a question about the uploaded files",
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