"""Chat API routes."""

import asyncio
import json
import time
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.models.requests import ChatRequest
from backend.models.responses import ChatResponse
from backend.services.chat_service import submit_question, stream_answer


router = APIRouter(prefix="/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Blocking route (unchanged)
# ---------------------------------------------------------------------------


@router.post("", response_model=ChatResponse)
def create_chat_response(payload: ChatRequest) -> ChatResponse:
    """Generate and persist a grounded answer for the supplied question."""
    try:
        message = submit_question(
            session_id=payload.session_id,
            question=payload.question,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return ChatResponse(**message)


# ---------------------------------------------------------------------------
# Streaming route
# ---------------------------------------------------------------------------


@router.post("/stream")
async def stream_chat_response(payload: ChatRequest) -> StreamingResponse:
    """Stream a grounded answer token-by-token using Server-Sent Events.

    The exchange is saved to Supabase exactly once after the full stream
    completes successfully.

    Each SSE event body is a JSON object with one of three shapes:

    - ``{"type": "chunk", "text": "<token>"}`` — incremental token text.
    - ``{"type": "done"}`` — stream finished; exchange persisted.
    - ``{"type": "error", "message": "<detail>"}`` — failure; no save.
    """
    return StreamingResponse(
        content=_sse_generator(payload.session_id, payload.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # Disable nginx proxy buffering so tokens flush immediately.
            "X-Accel-Buffering": "no",
        },
    )


async def _sse_generator(
    session_id: str, question: str
) -> AsyncGenerator[str, None]:
    """Encode ``stream_answer`` chunks as Server-Sent Events.

    Uses an async generator so FastAPI can flush each ``yield`` directly on
    the event loop without routing through the thread pool executor.
    ``stream_answer`` is a synchronous generator (the OpenAI SDK is sync),
    so it is iterated inside ``asyncio.to_thread`` to avoid blocking the
    event loop during the Supabase calls in ``_prepare_conversation``.

    JSON-encodes every payload so newlines inside tokens (e.g. code blocks)
    cannot corrupt the SSE framing.
    """
    # [DBG] Timestamps for the SSE layer
    t_sse_start = time.perf_counter()
    sse_chunk_count = 0
    print(f"[DBG][_sse_generator] Starting at t=0.000s", flush=True)

    try:
        # Run the sync generator in a thread.  We collect chunks via a queue
        # so the async generator can yield them on the event loop as they arrive.
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def _producer() -> None:
            """Drain stream_answer() in a thread and push chunks to the queue."""
            try:
                loop = asyncio.get_running_loop()  # [DBG] fixed: was get_event_loop()
                gen = stream_answer(session_id, question)

                def _next_chunk():
                    try:
                        return next(gen)
                    except StopIteration:
                        return None

                while True:
                    # [DBG] Measure round-trip cost of executor call
                    t_before = time.perf_counter()
                    chunk = await loop.run_in_executor(None, _next_chunk)
                    t_after = time.perf_counter()
                    print(
                        f"[DBG][_producer] run_in_executor returned in "
                        f"{(t_after - t_before) * 1000:.1f}ms  "
                        f"chunk={'None' if chunk is None else repr(chunk[:40])}",
                        flush=True,
                    )
                    await queue.put(chunk)
                    if chunk is None:
                        break
            except Exception as exc:
                await queue.put(exc)  # type: ignore[arg-type]

        producer_task = asyncio.create_task(_producer())

        while True:
            item = await queue.get()
            if item is None:
                # Stream finished normally.
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                print(
                    f"[DBG][_sse_generator] done event sent at "
                    f"t={(time.perf_counter() - t_sse_start):.3f}s "
                    f"total_chunks={sse_chunk_count}",
                    flush=True,
                )
                break
            if isinstance(item, Exception):
                raise item
            sse_chunk_count += 1
            now = time.perf_counter()
            print(
                f"[DBG][_sse_generator] yielding SSE chunk #{sse_chunk_count} "
                f"t={(now - t_sse_start):.3f}s repr={item!r}",
                flush=True,
            )
            yield f"data: {json.dumps({'type': 'chunk', 'text': item})}\n\n"

        await producer_task

    except ValueError as error:
        yield f"data: {json.dumps({'type': 'error', 'message': str(error)})}\n\n"
    except RuntimeError as error:
        yield f"data: {json.dumps({'type': 'error', 'message': str(error)})}\n\n"
