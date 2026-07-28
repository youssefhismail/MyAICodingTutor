"""FastAPI application entrypoint."""

from fastapi import FastAPI

from backend.api.chat import router as chat_router
from backend.api.sessions import router as sessions_router


app = FastAPI(
    title="MyAI Coding Tutor API",
    description="Backend API powering the AI Coding Tutor application.",
    version="1.0.0",
    openapi_tags=[
        {"name": "chat", "description": "Chat endpoints"},
        {"name": "sessions", "description": "Conversation management"},
    ],
)

app.include_router(chat_router)
app.include_router(sessions_router)


@app.get("/health")
def health() -> dict[str, str]:
	"""Return a lightweight health response."""
	return {"status": "ok"}
