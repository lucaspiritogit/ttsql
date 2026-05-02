from __future__ import annotations

import asyncio

from rich.spinner import Spinner
from textual.app import App, ComposeResult
from textual.events import Click
from textual.containers import Container, VerticalScroll
from textual.widgets import Input

from apps.client.api import stream_query
from apps.client.config import API_URL, QUERY_ENDPOINT
from apps.client.tui.rendering import (
    answer_panel,
    answer_spinner,
    canceled_panel,
    error_panel,
    format_response,
    thinking_panel,
    thinking_spinner,
    update_thinking_spinner,
    user_panel,
    welcome_panel,
)
from apps.client.tui.widgets import Message


class TextToSqlTui(App[None]):
    CSS = """
    Screen {
        layout: vertical;
        background: #111110;
        color: #E8E6E1;
    }

    #messages {
        height: 1fr;
        padding: 1 3 0 3;
        background: #111110;
    }

    #input_bar {
        height: 4;
        padding: 0 3;
        background: #171716;
        border-top: solid #2A2A28;
    }

    Input {
        width: 100%;
        height: 3;
        background: #171716;
        color: #E8E6E1;
        border: none;
    }

    Input:focus {
        border: none;
    }

    Input > .input--placeholder {
        color: #9A9690;
    }

    Message {
        margin-bottom: 1;
        background: #111110;
    }
    """

    BINDINGS = [
        ("escape", "cancel_query", "Cancel query"),
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+d", "quit", "Quit"),
    ]

    TITLE = "Text-to-SQL"
    SUB_TITLE = f"API: {API_URL}{QUERY_ENDPOINT}"
    ALLOW_SELECT = True
    ENABLE_SELECT_AUTO_SCROLL = True

    def __init__(self) -> None:
        super().__init__()
        self._query_task: asyncio.Task[None] | None = None
        self._active_response: Message | None = None
        self._active_answer: Message | None = None

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Message(welcome_panel()), id="messages")
        with Container(id="input_bar"):
            yield Input(id="prompt")

    def on_mount(self) -> None:
        self.call_after_refresh(self._focus_prompt)

    def on_click(self, event: Click) -> None:
        self._focus_prompt()

    def _focus_prompt(self) -> None:
        prompt = self.query_one("#prompt", Input)
        if not prompt.disabled:
            prompt.focus()

    def action_cancel_query(self) -> None:
        if self._query_task and not self._query_task.done():
            self._query_task.cancel()
        if self._active_response is not None:
            self._active_response.update(canceled_panel())
            self._scroll_to_end()
        if self._active_answer is not None:
            self._active_answer.update(canceled_panel())
            self._scroll_to_end()
        self._focus_prompt()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        prompt = event.value.strip()
        if not prompt:
            return

        if self._query_task and not self._query_task.done():
            self._query_task.cancel()
            if self._active_response is not None:
                self._active_response.update(canceled_panel(
                    "Canceled because a new query was submitted."))
                self._scroll_to_end()
            if self._active_answer is not None:
                self._active_answer.update(canceled_panel(
                    "Canceled because a new query was submitted."))
                self._scroll_to_end()

        input_widget = event.input
        input_widget.value = ""
        input_widget.focus()

        self._append(Message(user_panel(prompt)))
        spinner = thinking_spinner()
        thinking = Message(thinking_panel(spinner))
        self._append(thinking)
        self._active_response = thinking
        self._query_task = asyncio.create_task(
            self._run_query(prompt, thinking, spinner, input_widget))

    async def _run_query(self, prompt: str, thinking: Message, spinner: Spinner, input_widget: Input) -> None:
        response_payload: dict[str, object] = {"question": prompt}
        stream_error = False
        spinner_active = [True]
        answer_message: Message | None = None
        answer_active = [False]
        answer_spin = answer_spinner()

        def refresh_spinner() -> None:
            if spinner_active[0]:
                self._update_message(thinking, thinking_panel(spinner), scroll=False)
            if answer_active[0] and answer_message is not None:
                self._update_message(
                    answer_message, thinking_panel(answer_spin), scroll=False)

        spinner_timer = self.set_interval(0.125, refresh_spinner)

        try:
            async for event_name, data in stream_query(prompt):
                if event_name == "status":
                    message = data.get("message", "Working") if isinstance(
                        data, dict) else str(data)
                    status_text = str(message).replace("_", " ").capitalize()
                    if message == "explaining_result":
                        spinner_active[0] = False
                        if answer_message is None:
                            answer_message = Message(
                                thinking_panel(answer_spin))
                            self._append(answer_message)
                            self._active_answer = answer_message
                        answer_active[0] = True
                        update_thinking_spinner(answer_spin, status_text)
                        self._update_message(
                            answer_message, thinking_panel(answer_spin), scroll=False)
                    else:
                        update_thinking_spinner(spinner, status_text)
                        spinner_active[0] = True
                        self._update_message(thinking, thinking_panel(spinner), scroll=False)
                elif event_name == "sql" and isinstance(data, dict):
                    spinner_active[0] = False
                    response_payload["sql"] = data.get("sql", "")
                    self._update_message(
                        thinking, format_response(response_payload))
                elif event_name == "rows" and isinstance(data, dict):
                    spinner_active[0] = False
                    response_payload["rows"] = data.get("rows", [])
                    self._update_message(
                        thinking, format_response(response_payload))
                elif event_name == "answer" and isinstance(data, dict):
                    answer_active[0] = False
                    answer = str(data.get("answer", ""))
                    if answer_message is None:
                        answer_message = Message(answer_panel(answer))
                        self._append(answer_message)
                    else:
                        self._update_message(
                            answer_message, answer_panel(answer))
                    self._active_answer = None
                elif event_name == "error":
                    spinner_active[0] = False
                    stream_error = True
                    message = data.get("message", data) if isinstance(
                        data, dict) else data
                    self._update_message(thinking, error_panel(str(message)))
                    if answer_message is not None:
                        answer_active[0] = False
                        self._update_message(
                            answer_message, error_panel(str(message)))
                elif event_name == "done" and not stream_error:
                    spinner_active[0] = False
                    if isinstance(data, dict) and data.get("ok") is False:
                        self._update_message(thinking, error_panel(
                            "The query stream ended with an error."))
        except asyncio.CancelledError:
            spinner_active[0] = False
            self._update_message(thinking, canceled_panel())
            if answer_message is not None:
                answer_active[0] = False
                self._update_message(answer_message, canceled_panel())
        except Exception as exc:  # noqa: BLE001 - user-facing TUI should show all request failures
            spinner_active[0] = False
            self._update_message(thinking, error_panel(str(exc)))
            if answer_message is not None:
                answer_active[0] = False
                self._update_message(answer_message, error_panel(str(exc)))
        finally:
            spinner_active[0] = False
            spinner_timer.stop()
            if self._active_response is thinking:
                self._active_response = None
            if self._active_answer is answer_message:
                self._active_answer = None
            if self._query_task is asyncio.current_task():
                self._query_task = None
            input_widget.focus()

    def _append(self, message: Message) -> None:
        messages = self.query_one("#messages", VerticalScroll)
        messages.mount(message)
        self._scroll_to_end()

    def _update_message(self, message: Message, renderable: object, *, scroll: bool = True) -> None:
        message.update(renderable)
        if scroll:
            self._scroll_to_end()

    def _scroll_to_end(self) -> None:
        messages = self.query_one("#messages", VerticalScroll)
        messages.scroll_end(animate=False)
