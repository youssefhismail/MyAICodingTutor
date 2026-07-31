from collections.abc import Iterator
import time

from openai import OpenAI

from backend.config import DEPLOYMENT_NAME, FOUNDRY_API_KEY, FOUNDRY_ENDPOINT


def _get_base_url(endpoint: str) -> str:
    """Return one OpenAI v1 base URL from either supported endpoint form."""
    normalized_endpoint = endpoint.rstrip("/")
    if normalized_endpoint.endswith("/openai/v1"):
        return f"{normalized_endpoint}/"
    return f"{normalized_endpoint}/openai/v1/"


def _make_client() -> OpenAI:
    """Create a configured Azure AI Foundry OpenAI client.

    Raises:
        RuntimeError: if any required environment variable is missing.
    """
    if not FOUNDRY_ENDPOINT or not FOUNDRY_API_KEY or not DEPLOYMENT_NAME:
        raise RuntimeError(
            "Azure AI Foundry is not configured. Set FOUNDRY_ENDPOINT, "
            "FOUNDRY_API_KEY, and DEPLOYMENT_NAME."
        )
    return OpenAI(
        base_url=_get_base_url(FOUNDRY_ENDPOINT),
        api_key=FOUNDRY_API_KEY,
        default_headers={"api-key": FOUNDRY_API_KEY},
    )


def ask_llm(prompt: str) -> str:
    """Send one prompt to Azure AI Foundry and return its text answer."""
    client = _make_client()

    try:
        response = client.responses.create(
            model=DEPLOYMENT_NAME,
            input=prompt,
        )
    except Exception as error:
        raise RuntimeError(f"Azure AI Foundry request failed: {error}") from error

    answer = response.output_text
    if not answer:
        raise RuntimeError("Azure AI Foundry returned an empty answer.")
    return answer


def stream_llm(prompt: str) -> Iterator[str]:
    """Stream text tokens from Azure AI Foundry one chunk at a time.

    Yields each text delta as it arrives from the model.  The underlying HTTP
    connection is closed automatically when the generator is exhausted or
    explicitly closed (e.g. on client disconnect).

    Raises:
        RuntimeError: if the connection fails or the model returns no tokens.
    """
    client = _make_client()
    stream = None

    # [DBG] Record when we start the Azure request
    t_request_start = time.perf_counter()
    print(f"[DBG][stream_llm] Sending request to Azure at t=0.000s", flush=True)

    try:
        stream = client.responses.create(
            model=DEPLOYMENT_NAME,
            input=prompt,
            stream=True,
        )

        # [DBG] Record time-to-first-event (includes Azure's prefill latency)
        t_first_event: float | None = None
        event_count = 0
        delta_count = 0

        for event in stream:
            now = time.perf_counter()

            # [DBG] Log EVERY event type so we can see what Azure actually sends
            event_type = getattr(event, "type", "<no type>")
            if t_first_event is None:
                t_first_event = now
                print(
                    f"[DBG][stream_llm] First event arrived at "
                    f"t={(now - t_request_start):.3f}s  type={event_type!r}",
                    flush=True,
                )
            event_count += 1

            if event_type == "response.output_text.delta":
                delta = getattr(event, "delta", "")
                if delta:
                    delta_count += 1
                    print(
                        f"[DBG][stream_llm] delta #{delta_count} "
                        f"t={(now - t_request_start):.3f}s "
                        f"len={len(delta)} repr={delta!r}",
                        flush=True,
                    )
                    yield delta
            else:
                # [DBG] Non-delta event – log briefly so we don't miss anything
                print(
                    f"[DBG][stream_llm] non-delta event #{event_count} "
                    f"t={(now - t_request_start):.3f}s type={event_type!r}",
                    flush=True,
                )

        print(
            f"[DBG][stream_llm] Stream exhausted. "
            f"total_events={event_count} delta_events={delta_count} "
            f"total_time={(time.perf_counter() - t_request_start):.3f}s",
            flush=True,
        )

    except Exception as error:
        raise RuntimeError(f"Azure AI Foundry streaming failed: {error}") from error
    finally:
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass
