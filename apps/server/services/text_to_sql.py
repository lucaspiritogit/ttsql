from __future__ import annotations

import asyncio

from apps.server.config import MAX_ROWS, MODEL_NAME
from apps.server.schema import SCHEMA_DESCRIPTION
from apps.server.services.ollama import generate
from apps.server.services.sql_guard import extract_sql, validate_sql


async def generate_sql(question: str) -> str:
    return await asyncio.to_thread(generate_sql_sync, question)


def generate_sql_sync(question: str) -> str:
    prompt = build_sql_prompt(question)
    raw = generate(
        model=MODEL_NAME,
        prompt=prompt,
        options={"temperature": 0, "num_predict": 128},
    )
    return validate_sql(extract_sql(raw))


def build_sql_prompt(question: str) -> str:
    return f"""
### Task
Generate one PostgreSQL SELECT query that answers the user's question.
Return only SQL. Do not return markdown, comments, explanations, or natural language.

### Database schema
{SCHEMA_DESCRIPTION}

### Constraints
- Use only the sales table and columns listed above.
- Use week_day for day-of-week filters, for example week_day = 'Friday'.
- For most bought / best-selling questions, rank by SUM(quantity).
- For highest revenue questions, rank by SUM(total).
- For most expensive / costs more questions, rank by MAX(unitary_price).
- Add LIMIT {MAX_ROWS} for row-returning queries; omit LIMIT only for single-row aggregate queries.

### Question
{question}

### SQL
""".strip()
