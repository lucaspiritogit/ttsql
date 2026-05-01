from __future__ import annotations

import json
from typing import Any

from fastapi.encoders import jsonable_encoder


def sse(event: str, data: Any) -> str:
    payload = json.dumps(jsonable_encoder(data), ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"
