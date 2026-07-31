"""Render Streamlit UI components."""

import streamlit as st


def render_chat(messages: list[dict[str, str]]) -> None:
    """Render the full conversation history from session state.

    Deliberately has no heading — the two-column layout makes the purpose
    of each panel self-evident, and removing the heading reclaims vertical
    space so more messages fit without scrolling.
    """
    for message in messages:
        with st.chat_message("user"):
            st.markdown(message["question"])

        with st.chat_message("assistant"):
            st.markdown(message["answer"])