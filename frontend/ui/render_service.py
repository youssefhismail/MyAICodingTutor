"""Render Streamlit UI components."""

import streamlit as st


def render_chat(messages: list[dict[str, str]]) -> None:
    """
    Render the conversation history.
    """
    st.subheader("Conversation")

    for message in messages:
        with st.chat_message("user"):
            st.markdown(message["question"])

        with st.chat_message("assistant"):
            st.markdown(message["answer"])