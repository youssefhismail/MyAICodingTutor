from openai import OpenAI

from config import DEPLOYMENT_NAME, FOUNDRY_API_KEY, FOUNDRY_ENDPOINT


def ask_llm(prompt: str) -> str:
    if not FOUNDRY_ENDPOINT or not FOUNDRY_API_KEY or not DEPLOYMENT_NAME:
        raise RuntimeError(
            "Azure AI Foundry is not configured. Set FOUNDRY_ENDPOINT, "
            "FOUNDRY_API_KEY, and DEPLOYMENT_NAME."
        )
    if "/api/projects/" not in FOUNDRY_ENDPOINT:
        raise RuntimeError(
            "FOUNDRY_ENDPOINT must be the complete Foundry Project endpoint. "
            "Copy it from Foundry and use the form "
            "https://<account>.services.ai.azure.com/api/projects/<project-name>."
        )
    base_url = f"{FOUNDRY_ENDPOINT}/openai/v1"
    client = OpenAI(
        base_url=base_url,
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
