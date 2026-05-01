from __future__ import annotations

import os

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
QUERY_ENDPOINT = os.getenv("QUERY_ENDPOINT", "/query/stream")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
