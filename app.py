import streamlit as st
from uuid import uuid4

from config import DEFAULT_SYSTEM_PROMPT
from services.chat_service import delete_messages, load_messages, submit_question
from services.file_service import load_file
from services.render_service import render_chat


def initialise_session() -> None:
    st.session_state.setdefault("session_id", str(uuid4()))
    st.session_state.setdefault("context", "")
    st.session_state.setdefault("filename", "")
    st.session_state.setdefault("messages", None)

    if st.session_state.messages is None:
        try:
            st.session_state.messages = load_messages(st.session_state.session_id)
        except RuntimeError:
            # The app can still answer questions when Supabase is not yet set up.
            st.session_state.messages = []


def main() -> None:
    initialise_session()

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
    )

    if uploaded_file is not None:
        try:
            st.session_state.context = load_file(uploaded_file)
            st.session_state.filename = uploaded_file.name
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
