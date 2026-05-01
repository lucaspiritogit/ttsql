from __future__ import annotations

import re

from apps.server.config import MAX_ROWS


def extract_sql(model_output: str) -> str:
    output = model_output.strip()

    # Match SQL wrapped in a markdown fence, with or without the optional `sql` language tag.
    # Example: ```sql SELECT * FROM sales ``` or ``` SELECT * FROM sales ```.
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", output, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        output = fenced.group(1).strip()

    # If the model returned extra text before the query, keep everything from the first
    # standalone SELECT keyword onward. `\b` prevents matching words like "selected".
    match = re.search(r"\bselect\b.*", output, flags=re.IGNORECASE | re.DOTALL)
    if match:
        output = match.group(0).strip()

    return output.strip().rstrip(";").strip()


def validate_sql(sql: str) -> str:
    if not sql:
        raise ValueError("I could not generate a SQL query for that input. Please ask a question about the sales data.")

    # Collapse newlines, tabs, and repeated spaces so keyword checks work consistently.
    normalized = re.sub(r"\s+", " ", sql).strip()
    lowered = normalized.lower()

    if not lowered.startswith("select"):
        raise ValueError("I could not turn that into a safe SQL SELECT query. Please ask a question about the sales data, for example: 'What is the most bought product on Fridays?'")
    if ";" in normalized:
        raise ValueError("I can only run one safe SQL SELECT query at a time. Please simplify the question and try again.")

    forbidden = {"insert", "update", "delete", "drop", "alter", "create", "truncate", "copy", "grant", "revoke"}
    # Extract word-like SQL tokens so we can block dangerous keywords only as complete words.
    tokens = set(re.findall(r"\b[a-z_]+\b", lowered))
    blocked = sorted(tokens & forbidden)
    if blocked:
        raise ValueError("That request produced unsafe SQL, so it was blocked. Please ask a read-only question about the sales data.")

    # Detect an existing standalone LIMIT clause before appending the default row cap.
    if not re.search(r"\blimit\b", lowered):
        normalized = f"{normalized} LIMIT {MAX_ROWS}"

    return normalized
