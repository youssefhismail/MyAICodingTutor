import streamlit as st
from uuid import uuid4

from config import DEFAULT_SYSTEM_PROMPT
from services.chat_service import (
    delete_messages,
    load_conversation_summaries,
    load_messages,
    submit_question,
)
from services.file_service import load_file
from services.render_service import render_chat
from services.sidebar_service import render_sidebar


def initialise_session() -> None:
    st.session_state.setdefault("session_id", str(uuid4()))
    st.session_state.setdefault("context", "")
    st.session_state.setdefault("filename", "")
    st.session_state.setdefault("messages", None)
    st.session_state.setdefault("session_contexts", {})
    st.session_state.setdefault("uploader_key", 0)

    if st.session_state.messages is None:
        try:
            st.session_state.messages = load_messages(st.session_state.session_id)
        except RuntimeError:
            # The app can still answer questions when Supabase is not yet set up.
            st.session_state.messages = []

    restore_session_assets(st.session_state.session_id)


def cache_active_session_assets() -> None:
    if st.session_state.context:
        st.session_state.session_contexts[st.session_state.session_id] = {
            "context": st.session_state.context,
            "filename": st.session_state.filename,
        }


def restore_session_assets(session_id: str) -> None:
    cached = st.session_state.session_contexts.get(session_id)
    if cached:
        st.session_state.context = cached.get("context", "")
        st.session_state.filename = cached.get("filename", "")


def start_new_chat() -> None:
    cache_active_session_assets()
    st.session_state.session_id = str(uuid4())
    st.session_state.context = ""
    st.session_state.filename = ""
    st.session_state.messages = []
    st.session_state.uploader_key += 1


def open_conversation(session_id: str) -> None:
    cache_active_session_assets()
    st.session_state.session_id = session_id
    try:
        st.session_state.messages = load_messages(session_id)
    except RuntimeError:
        st.session_state.messages = []

    st.session_state.uploader_key += 1
    st.session_state.context = ""
    st.session_state.filename = ""
    restore_session_assets(session_id)
    if not st.session_state.filename and st.session_state.messages:
        st.session_state.filename = st.session_state.messages[0].get("filename", "")


def render_sidebar(conversations: list[dict[str, str]]) -> None:
    with st.sidebar:
        st.title("Chats")

        if st.button("New Chat", use_container_width=True):
            start_new_chat()

        st.divider()
        st.subheader("Previous conversations")

        previous_conversations = [
            conversation
            for conversation in conversations
            if conversation["session_id"] != st.session_state.session_id
        ]

        if not previous_conversations:
            st.caption("No saved conversations yet.")
            return

        for index, conversation in enumerate(previous_conversations):
            label = conversation["first_question"] or conversation["filename"] or "Untitled conversation"
            if st.button(
                label,
                key=f"conversation_{conversation['session_id']}_{index}",
                use_container_width=True,
            ):
                open_conversation(conversation["session_id"])


def main() -> None:
    initialise_session()

    try:
        conversations = load_conversation_summaries()
    except RuntimeError:
        conversations = []

    render_sidebar(conversations)

    st.subheader("📂 Upload File")
    uploaded_file = st.file_uploader(
        "Upload a file",
        type=["py", "js", "ts", "md", "txt", "json", "html", "css", "ipynb"],
        label_visibility="collapsed",
        key=f"file_uploader_{st.session_state.uploader_key}",
    )

    if uploaded_file is not None:
        try:
            st.session_state.context = load_file(uploaded_file)
            st.session_state.filename = uploaded_file.name
            cache_active_session_assets()
        except ValueError as error:
            st.session_state.context = ""
            st.session_state.filename = ""
            st.error(str(error))

    st.subheader("System Prompt")
    system_prompt = st.text_area(
        "System Prompt",
        value=DEFAULT_SYSTEM_PROMPT,
        label_visibility="collapsed",
    )

    st.subheader("Chat")
    with st.form("chat_form", clear_on_submit=True):
        question = st.text_input("You", placeholder="Ask a question about the uploaded file")
        send = st.form_submit_button("Send")

    if st.button("Clear Conversation"):
        try:
            delete_messages(st.session_state.session_id)
            st.session_state.messages = []
            st.rerun()
        except RuntimeError as error:
            st.error(str(error))

    if send:
        try:
            with st.spinner("Thinking..."):
                message = submit_question(
                    session_id=st.session_state.session_id,
                    filename=st.session_state.filename,
                    system_prompt=system_prompt,
                    context=st.session_state.context,
                    chat_history=st.session_state.messages,
                    question=question,
                )

            st.session_state.messages.append(message)
        except ValueError as error:
            st.error(str(error))
        except RuntimeError as error:
            st.error(str(error))

    render_chat(st.session_state.messages)


if __name__ == "__main__":
    main()
