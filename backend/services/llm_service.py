from openai import OpenAI

from backend.config import DEPLOYMENT_NAME, FOUNDRY_API_KEY, FOUNDRY_ENDPOINT


def _get_base_url(endpoint: str) -> str:
    """Return one OpenAI v1 base URL from either supported endpoint form."""
    normalized_endpoint = endpoint.rstrip("/")
    if normalized_endpoint.endswith("/openai/v1"):
        return f"{normalized_endpoint}/"
    return f"{normalized_endpoint}/openai/v1/"


def ask_llm(prompt: str) -> str:
    """Send one prompt to Azure AI Foundry and return its text answer."""
    if not FOUNDRY_ENDPOINT or not FOUNDRY_API_KEY or not DEPLOYMENT_NAME:
        raise RuntimeError(
            "Azure AI Foundry is not configured. Set FOUNDRY_ENDPOINT, "
            "FOUNDRY_API_KEY, and DEPLOYMENT_NAME."
        )
    client = OpenAI(
        base_url=_get_base_url(FOUNDRY_ENDPOINT),
        api_key=FOUNDRY_API_KEY,
        default_headers={"api-key": FOUNDRY_API_KEY},
    )

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
