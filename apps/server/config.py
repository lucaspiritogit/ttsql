from __future__ import annotations

import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://app:app@localhost:5432/app")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "pxlksr/defog_sqlcoder-7b-2:Q2_KS")
EXPLANATION_MODEL_NAME = os.getenv("EXPLANATION_MODEL_NAME", "qwen2.5-coder:1.5b")
QUERY_TIMEOUT_MS = int(os.getenv("QUERY_TIMEOUT_MS", "10000"))
MAX_ROWS = int(os.getenv("MAX_ROWS", "100"))
