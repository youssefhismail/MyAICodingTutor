"""Build the grounded prompt sent to the language model."""

import logging


logger = logging.getLogger(__name__)

# Set to True only while diagnosing prompt/context issues. It is disabled for
# normal use because it can log uploaded-file and conversation content.
DEBUG_CONVERSATION_CONTEXT = False


def build_prompt(
    system_prompt: str,
    context: str,
    chat_history: list[dict[str, str]],
    question: str,
) -> str:
    history_text = _format_chat_history(chat_history)

    prompt = f"""SYSTEM INSTRUCTIONS
{system_prompt}

SOURCE RULES
1. For file-related questions, the Uploaded File is the primary and only
   source of truth. Do not invent information that is absent from it.
2. For questions about earlier messages, the Conversation History is the
   source of truth. It contains only messages that occurred before the
   Current Question.
3. "What was my previous question?", "What did you answer earlier?", and
   "Summarize our conversation" must be answered from Conversation History.
   Never treat the Current Question as a previous question or earlier message.
4. If the needed information is in neither relevant source, say so plainly.

--- UPLOADED FILE ---
{context}
--- END UPLOADED FILE ---

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

    return "\n\n".join(
        f"User: {message['question']}\nAssistant: {message['answer']}"
        for message in chat_history
    )
