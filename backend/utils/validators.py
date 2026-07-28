"""Small reusable input validators."""


def require_text(value: str, field_name: str) -> str:
    """Return stripped text or raise ValueError when it is blank."""
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} cannot be empty.")
    return text
