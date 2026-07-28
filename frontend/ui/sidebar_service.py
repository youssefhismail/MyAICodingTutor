"""Render the Streamlit sidebar."""

import streamlit as st


def render_sidebar(
    conversations: list[dict[str, str]],
    current_session_id: str,
    on_new_chat,
    on_open_conversation,
) -> None:
    """Render the conversation sidebar."""

    with st.sidebar:
        st.title("Chats")

        if st.button("➕ New Chat", use_container_width=True):
            on_new_chat()

        st.divider()
        st.subheader("Previous Conversations")

        previous = [
            conversation
            for conversation in conversations
            if conversation["session_id"] != current_session_id
        ]

        if not previous:
            st.caption("No saved conversations yet.")
            return

        for index, conversation in enumerate(previous):
            label = (
                conversation["first_question"]
                or conversation["filename"]
                or "Untitled Conversation"
            )

            if len(label) > 45:
                label = label[:42] + "..."

            if st.button(
                label,
                key=f"{conversation['session_id']}_{index}",
                use_container_width=True,
            ):
                on_open_conversation(conversation["session_id"])