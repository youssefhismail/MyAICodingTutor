"""Application configuration loaded from environment variables."""

from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent


load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env", override=False)


FOUNDRY_ENDPOINT = os.getenv("FOUNDRY_ENDPOINT", "").rstrip("/")
FOUNDRY_API_KEY = os.getenv("FOUNDRY_API_KEY", "")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024)))

DEFAULT_SYSTEM_PROMPT = """
You are an expert programming assistant.

Use the uploaded file as the primary source of truth.

If the question cannot be answered from the uploaded file, say that the information is unavailable instead of inventing an answer.

Do not make assumptions beyond what appears in the uploaded file.

If the user asks about previous messages in the current conversation, answer using the conversation history.

If the answer cannot be found in either the uploaded file or the conversation history, clearly say so instead of making something up.
""".strip()
