from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from apps.server.config import DATABASE_URL, MAX_ROWS, QUERY_TIMEOUT_MS


def execute_sql(sql: str) -> list[dict[str, Any]]:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(QUERY_TIMEOUT_MS),))
            cursor.execute(sql)
            return list(cursor.fetchmany(MAX_ROWS))
