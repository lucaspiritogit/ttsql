from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str | None = Field(default=None, description="Natural language question")

    @property
    def text(self) -> str:
        return (self.question or "").strip()


class QueryResponse(BaseModel):
    question: str
    sql: str
    rows: list[dict[str, Any]]
    answer: str
