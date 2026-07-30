"""Build the grounded prompt sent to the language model."""

import logging


from backend.models.domain import DocumentContext

logger = logging.getLogger(__name__)

# Set to True only while diagnosing prompt/context issues. It is disabled for
# normal use because it can log uploaded-file and conversation content.
DEBUG_CONVERSATION_CONTEXT = False


def build_prompt(
    system_prompt: str,
    documents: list[DocumentContext],
    chat_history: list[dict[str, str]],
    question: str,
) -> str:
    history_text = _format_chat_history(chat_history)

    context = ""
    for doc in documents:
        filename = doc.filename
        content = doc.content.strip()
        if content:
            context += f"\n--- FILE: {filename} ---\n{content}\n--- END FILE ---\n"

    prompt = f"""SYSTEM INSTRUCTIONS
{system_prompt}

SOURCE RULES
1. For file-related questions, the Uploaded Files are the primary and only
   source of truth. Do not invent information that is absent from them.
2. For questions about earlier messages, the Conversation History is the
   source of truth. It contains only messages that occurred before the
   Current Question.
3. "What was my previous question?", "What did you answer earlier?", and
   "Summarize our conversation" must be answered from Conversation History.
   Never treat the Current Question as a previous question or earlier message.
4. If the needed information is in neither relevant source, say so plainly.

--- UPLOADED FILES ---
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
