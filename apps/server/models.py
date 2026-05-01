from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str | None = Field(default=None, description="Natural language question")

    @property
    def text(self) -> str:
        return (self.question or "").strip()
