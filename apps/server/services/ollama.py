from __future__ import annotations

from typing import Any

import requests

from apps.server.config import OLLAMA_URL


def generate(
    *,
    model: str,
    prompt: str,
    options: dict[str, Any],
    keep_alive: str | None = "30m",
    timeout: float = 120,
) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": options,
    }
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"model service error: {exc}") from exc

    return response.json().get("response", "")
