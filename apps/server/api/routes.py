from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from apps.server.database import execute_sql
from apps.server.models import QueryRequest
from apps.server.schema import SCHEMA_DESCRIPTION
from apps.server.services.result_explainer import explain_result
from apps.server.services.text_to_sql import generate_sql
from apps.server.api.sse import sse

router = APIRouter()


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Text-to-SQL API is running"}


@router.get("/schema")
def schema() -> dict[str, str]:
    return {"schema": SCHEMA_DESCRIPTION}


@router.post("/query/stream")
async def query_stream(request: QueryRequest) -> StreamingResponse:
    question = request.text
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    async def events() -> AsyncIterator[str]:
        try:
            yield sse("status", {"message": "thinking"})
            yield sse("status", {"message": "generating_sql"})
            sql = await generate_sql(question)
            yield sse("sql", {"sql": sql})

            yield sse("status", {"message": "executing_sql"})
            rows = await asyncio.to_thread(execute_sql, sql)
            yield sse("rows", {"rows": rows})

            yield sse("status", {"message": "explaining_result"})
            answer = await explain_result(question, sql, rows)
            yield sse("answer", {"answer": answer})

            yield sse("done", {"ok": True})
        except Exception as exc:
            yield sse("error", {"message": str(exc)})
            yield sse("done", {"ok": False})

    return StreamingResponse(events(), media_type="text/event-stream")
