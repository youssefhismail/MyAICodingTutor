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
            if "metadata" in message and message["metadata"]:
                render_retrieval_metadata(message["metadata"])


def render_retrieval_metadata(metadata: dict) -> None:
    """Render Phase 4 Sources, Transparency, and Debug UI."""
    if not metadata:
        return

    retrieved_chunks = metadata.get("retrieved_chunks", [])
    if not retrieved_chunks:
        return
        
    st.markdown("---")
    
    # Phase 4.1 Sources
    st.markdown("**Sources**")
    for r_chunk in retrieved_chunks:
        filename = r_chunk.get("filename", "Unknown")
        chunk_data = r_chunk.get("chunk", {})
        seq = chunk_data.get("sequence_number", 0)
        start = chunk_data.get("start_offset", 0)
        end = chunk_data.get("end_offset", 0)
        
        st.markdown(f"- `{filename}` (Chunk {seq}, Characters {start}–{end})")
        
    # Phase 4.2 Transparency
    st.markdown("**Retrieval Transparency**")
    stats = metadata.get("stats", {})
    st.caption(
        f"Retrieved: {stats.get('retrieved', 0)} | "
        f"Passed Threshold: {stats.get('after_threshold', 0)} | "
        f"Duplicates Removed: {stats.get('duplicates_removed', 0)} | "
        f"Final Used: {len(retrieved_chunks)}"
    )
    for r_chunk in retrieved_chunks:
        st.caption(f"- `{r_chunk.get('filename', 'Unknown')}` (Distance: {r_chunk.get('distance', 0.0):.3f})")

    # Phase 4.3 Debug Mode
    if st.session_state.get("debug_retrieval", False):
        with st.expander("🛠️ Inspect Retrieved Chunks"):
            for r_chunk in retrieved_chunks:
                filename = r_chunk.get("filename", "Unknown")
                chunk_data = r_chunk.get("chunk", {})
                seq = chunk_data.get("sequence_number", 0)
                st.markdown(f"**{filename}** (Chunk {seq})")
                st.code(chunk_data.get("content", ""), language="text")