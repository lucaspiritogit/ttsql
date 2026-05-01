from __future__ import annotations

from typing import Any

from rich import box
from rich.console import Group, RenderableType
from rich.json import JSON
from rich.panel import Panel
from rich.pretty import Pretty
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

BORDER = "#2A2A28"
TEXT = "#E8E6E1"
MUTED = "#9A9690"
CANVAS = "#111110"
GREEN_TEXT = "#9EB89B"
RED_TEXT = "#D09A96"


def user_panel(prompt: str) -> Panel:
    return _panel(Text(prompt, style=TEXT), title="Question", border_style=BORDER)


def thinking_spinner(message: str = "Thinking. Generating SQL and querying the database.") -> Spinner:
    return Spinner("dots", Text(message, style=f"bold {GREEN_TEXT}"), style=GREEN_TEXT)


def answer_spinner(message: str = "Writing answer...") -> Spinner:
    return Spinner("dots", Text(message, style=f"bold {GREEN_TEXT}"), style=GREEN_TEXT)


def update_thinking_spinner(spinner: Spinner, message: str) -> None:
    spinner.update(text=Text(message, style=f"bold {GREEN_TEXT}"))


def thinking_panel(renderable: RenderableType | None = None) -> Panel:
    return _panel(renderable or thinking_spinner(), title="Status", border_style=BORDER)


def error_panel(message: str) -> Panel:
    return _panel(Text(message, style=RED_TEXT), title="Error", border_style=RED_TEXT)


def canceled_panel(message: str = "Canceled.") -> Panel:
    return _panel(Text(message, style=MUTED), title="Canceled", border_style=BORDER)


def answer_panel(answer: str) -> Panel:
    return _panel(Text(answer, style=f"bold {TEXT}"), border_style=BORDER)


def format_response(payload: Any) -> Panel:
    if isinstance(payload, dict):
        sql = payload.get("sql") or payload.get(
            "query") or payload.get("generated_sql")
        rows = payload.get("rows") or payload.get(
            "result") or payload.get("results")

        sections: list[RenderableType] = []
        if sql:
            sections.append(_section_label("Generated SQL"))
            sections.append(_sql_block(str(sql)))
        if rows is not None:
            sections.append(_section_label("Result"))
            sections.append(_rows_block(rows))

        if sections:
            return _panel(Group(*sections), border_style=BORDER)

        return _panel(JSON.from_data(payload), border_style=BORDER)

    return _panel(Text(str(payload), style=TEXT), border_style=BORDER)


def welcome_panel() -> Panel:
    body = Group(
        Text("Text-to-SQL workspace", style=f"bold {TEXT}"),
        Text("Ask a question in plain English. The app returns generated SQL, result rows, and a short explanation.", style=MUTED),
        Text("Press Enter to send. Ctrl+C to quit.", style=MUTED),
    )
    return _panel(body, title="Ready", border_style=BORDER)


def _section_label(label: str) -> Text:
    return Text(f"\n{label.upper()}", style=f"bold {MUTED}")


def _sql_block(sql: str) -> Panel:
    syntax = Syntax(
        sql,
        "sql",
        theme="ansi_dark",
        word_wrap=True,
        background_color=CANVAS,
    )
    return _panel(syntax, border_style=BORDER, padding=(0, 1))


def _rows_block(rows: Any) -> RenderableType:
    if isinstance(rows, list) and rows and all(isinstance(row, dict) for row in rows):
        return _rows_table(rows)
    return Pretty(rows)


def _rows_table(rows: list[dict[str, Any]]) -> Table:
    columns = list(rows[0].keys())
    table = Table(
        box=box.SIMPLE_HEAD,
        show_lines=False,
        border_style=BORDER,
        header_style=f"bold {TEXT}",
        style=TEXT,
        pad_edge=False,
    )
    for column in columns:
        table.add_column(str(column), overflow="fold")
    for row in rows:
        table.add_row(*(str(row.get(column, "")) for column in columns))
    return table


def _panel(
    renderable: RenderableType,
    *,
    title: str | None = None,
    border_style: str = BORDER,
    padding: tuple[int, int] = (1, 2),
) -> Panel:
    return Panel(
        renderable,
        title=title,
        title_align="left",
        border_style=border_style,
        box=box.SQUARE,
        padding=padding,
        style=TEXT,
    )
