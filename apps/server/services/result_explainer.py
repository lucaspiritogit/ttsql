from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi.encoders import jsonable_encoder

from apps.server.config import EXPLANATION_MODEL_NAME
from apps.server.services.ollama import generate


async def explain_result(question: str, sql: str, rows: list[dict[str, Any]]) -> str:
    return await asyncio.to_thread(explain_result_sync, question, sql, rows)


def explain_result_sync(question: str, sql: str, rows: list[dict[str, Any]]) -> str:
    prompt = build_explanation_prompt(question, sql, rows)
    return generate(
        model=EXPLANATION_MODEL_NAME,
        prompt=prompt,
        options={"temperature": 0.1, "num_predict": 120},
    ).strip()


def build_explanation_prompt(question: str, sql: str, rows: list[dict[str, Any]]) -> str:
    rows_json = json.dumps(jsonable_encoder(rows[:20]), ensure_ascii=False, indent=2)
    return f"""
You explain SQL query results to end users.
Write one short, direct natural-language answer to the user's question using only the SQL result rows.
Do not invent values. Do not mention that you are an AI model.
If the result is empty, say no matching data was found.

User question:
{question}

Generated SQL:
{sql}

SQL result rows:
{rows_json}

Answer:
""".strip()
