from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from apps.client.config import API_URL, QUERY_ENDPOINT, REQUEST_TIMEOUT_SECONDS


async def stream_query(prompt: str) -> AsyncIterator[tuple[str, Any]]:
    """Send a query to the SSE endpoint and yield decoded SSE events."""
    url = f"{API_URL}{QUERY_ENDPOINT}"
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        async with client.stream("POST", url, json={"question": prompt}) as response:
            response.raise_for_status()
            async for event, data in _iter_sse(response):
                yield event, data


async def _iter_sse(response: httpx.Response) -> AsyncIterator[tuple[str, Any]]:
    event = "message"
    data_lines: list[str] = []

    async for line in response.aiter_lines():
        if line == "":
            if data_lines:
                yield event, _parse_sse_data(data_lines)
            event = "message"
            data_lines = []
            continue

        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())

    if data_lines:
        yield event, _parse_sse_data(data_lines)


def _parse_sse_data(data_lines: list[str]) -> Any:
    raw_data = "\n".join(data_lines)
    try:
        return json.loads(raw_data)
    except json.JSONDecodeError:
        return raw_data
