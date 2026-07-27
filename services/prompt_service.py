def build_prompt(system_prompt: str, context: str, user_question: str) -> str:
    return f"""System:
{system_prompt}

Only answer using the uploaded file.
If the answer is not in the file, say so.

---------------------

Uploaded file:
{context}

---------------------

Question:
{user_question}
"""
