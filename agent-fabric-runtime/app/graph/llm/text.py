from typing import Any


def plain_text(content: Any) -> str:
    """Flatten model content to a string and drop Qwen `</think>` preamble if present."""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
        text = "".join(parts)
    else:
        text = "" if content is None else str(content)
    marker = "</think>"
    if marker in text:
        text = text.split(marker, 1)[-1]
    return text.strip()


# Tests historically imported the private name.
_plain_text = plain_text
