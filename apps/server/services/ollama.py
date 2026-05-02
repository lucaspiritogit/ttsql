from __future__ import annotations

from typing import Any

import requests

from apps.server.config import OLLAMA_URL


def generate(
    *,
    model: str,
    prompt: str,
    options: dict[str, Any],
    timeout: float = 120,
) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": options,
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = _ollama_error_detail(exc.response)
        raise RuntimeError(f"model service error: {detail}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"model service error: {exc}") from exc

    return response.json().get("response", "")


def _ollama_error_detail(response: requests.Response | None) -> str:
    if response is None:
        return "Ollama returned an error without a response."

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    error = payload.get("error") if isinstance(payload, dict) else None
    if error:
        return str(error)

    return f"{response.status_code} {response.reason} from {response.url}"
