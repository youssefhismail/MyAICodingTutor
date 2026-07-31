"""Build the grounded prompt sent to the language model."""

import logging


from backend.models.domain import RetrievedChunk

logger = logging.getLogger(__name__)

# Set to True only while diagnosing prompt/context issues. It is disabled for
# normal use because it can log uploaded-file and conversation content.
DEBUG_CONVERSATION_CONTEXT = False


def build_prompt(
    system_prompt: str,
    retrieved_chunks: list[RetrievedChunk],
    chat_history: list[dict[str, str]],
    question: str,
) -> str:
    history_text = _format_chat_history(chat_history)

    context = ""
    for r_chunk in retrieved_chunks:
        filename = r_chunk.filename
        seq = r_chunk.chunk.sequence_number
        start_off = r_chunk.chunk.start_offset
        end_off = r_chunk.chunk.end_offset
        content = r_chunk.chunk.content.strip()
        if content:
            context += (
                f"\nFile: {filename}\n"
                f"Chunk: {seq}\n"
                f"Start Offset: {start_off}\n"
                f"End Offset: {end_off}\n"
                f"{content}\n"
                f"----------------\n"
            )

    prompt = f"""SYSTEM INSTRUCTIONS
{system_prompt}

SOURCE RULES
1. The retrieved context is the primary source of truth for file-related questions.
2. If the answer cannot be determined from the retrieved context, clearly state that rather than inventing information.
3. For questions about earlier messages, the Conversation History is the
   source of truth. It contains only messages that occurred before the
   Current Question.
4. "What was my previous question?", "What did you answer earlier?", and
   "Summarize our conversation" must be answered from Conversation History.
   Never treat the Current Question as a previous question or earlier message.
5. If the needed information is in neither relevant source, say so plainly.

--- UPLOADED FILES (RETRIEVED CONTEXT) ---
{context}
--- END UPLOADED FILES ---

--- CONVERSATION HISTORY (PRIOR MESSAGES ONLY) ---
{history_text}
--- END CONVERSATION HISTORY ---

--- CURRENT QUESTION ---
{question}
--- END CURRENT QUESTION ---
"""

    if DEBUG_CONVERSATION_CONTEXT:
        logger.info(
            "Conversation-context debug before Azure request:\n"
            "message_count=%d\n"
            "formatted_history:\n%s\n"
            "final_prompt:\n%s",
            len(chat_history),
            history_text,
            prompt,
        )

    return prompt


def _format_chat_history(chat_history: list[dict[str, str]]) -> str:
    if not chat_history:
        return "No prior conversation."

    lines: list[str] = []
    for message in chat_history:
        role = message.get("role", "user")
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {message.get('content', '')}")

    return "\n\n".join(lines)
