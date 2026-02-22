"""FastAPI application with WebSocket bridge for browser-based play."""

from __future__ import annotations

import asyncio
import io
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from rich.console import Console

from wallstreet.cli.app import run_game
from wallstreet.models.game import GameConfig

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Wall Street War Room")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index() -> FileResponse:
    """Serve the main HTML page."""
    return FileResponse(str(STATIC_DIR / "index.html"))


class WebSocketBridge:
    """Bridges the synchronous game loop I/O with an async WebSocket.

    The game loop runs in a background thread. Rich Console writes to a
    StringIO buffer; ``flush_output()`` sends the buffered ANSI text to
    the browser. ``sync_input()`` blocks the game thread until the
    browser sends a line of text.
    """

    def __init__(self, ws: WebSocket, loop: asyncio.AbstractEventLoop) -> None:
        self.ws = ws
        self.loop = loop
        self.input_queue: asyncio.Queue[str] = asyncio.Queue()
        self.output_buffer = io.StringIO()
        self.console = Console(
            file=self.output_buffer,
            force_terminal=True,
            color_system="truecolor",
            width=120,
        )

    # ── output ────────────────────────────────────────────────────────

    def flush_output(self) -> None:
        """Send buffered ANSI output to the WebSocket (game thread)."""
        text = self.output_buffer.getvalue()
        if text:
            future = asyncio.run_coroutine_threadsafe(
                self.ws.send_text(text), self.loop
            )
            future.result(timeout=10)
            self.output_buffer.truncate(0)
            self.output_buffer.seek(0)

    # ── input ─────────────────────────────────────────────────────────

    def sync_input(self, prompt: str = "") -> str:
        """Blocking input called from the game thread.

        Writes the prompt to the output buffer, flushes it, then waits
        for the browser to send a line.
        """
        if prompt:
            self.console.print(prompt, end="")
        self.flush_output()
        future = asyncio.run_coroutine_threadsafe(
            self.input_queue.get(), self.loop
        )
        return future.result(timeout=600)

    def sync_confirm(self, prompt: str) -> bool:
        """Blocking yes/no confirm called from the game thread."""
        if prompt:
            self.console.print(f"{prompt} [y/n] ", end="")
        self.flush_output()
        future = asyncio.run_coroutine_threadsafe(
            self.input_queue.get(), self.loop
        )
        answer = future.result(timeout=300).strip().lower()
        return answer in ("y", "yes")


@app.websocket("/ws/play")
async def play_game_ws(ws: WebSocket) -> None:
    """WebSocket endpoint: one game session per connection."""
    await ws.accept()

    # Parse config from query params
    params = ws.query_params
    seed = int(params.get("seed", "0"))
    name = params.get("name", "Player")
    weeks = int(params.get("weeks", "3"))
    capital = float(params.get("capital", "1000000"))

    loop = asyncio.get_event_loop()
    bridge = WebSocketBridge(ws, loop)

    config = GameConfig(seed=seed, player_name=name, total_weeks=weeks, starting_cash=capital)

    async def receive_loop() -> None:
        """Receive messages from browser and feed them to the game thread."""
        try:
            while True:
                data = await ws.receive_text()
                if data == "":
                    continue  # ignore keepalive pings
                await bridge.input_queue.put(data)
        except WebSocketDisconnect:
            # Push a sentinel so sync_input unblocks
            await bridge.input_queue.put("")

    recv_task = asyncio.create_task(receive_loop())

    async def keepalive_loop() -> None:
        """Send WebSocket pings every 30s to prevent proxy idle timeouts."""
        try:
            while True:
                await asyncio.sleep(30)
                await ws.send_bytes(b"")  # empty ping frame
        except Exception:
            pass

    keepalive_task = asyncio.create_task(keepalive_loop())

    try:
        await asyncio.to_thread(
            run_game,
            config,
            con=bridge.console,
            input_fn=bridge.sync_input,
            confirm_fn=bridge.sync_confirm,
            flush_fn=bridge.flush_output,
        )
        # Final flush to ensure all output reaches the client
        bridge.flush_output()
        await ws.send_text("\r\n\x1b[1;32mGame complete! Refresh to play again.\x1b[0m\r\n")
    except WebSocketDisconnect:
        logger.info("Client disconnected mid-game")
    except Exception:
        logger.exception("Game error")
        try:
            await ws.send_text("\r\n\x1b[1;31mServer error. Please refresh.\x1b[0m\r\n")
        except Exception:
            pass
    finally:
        keepalive_task.cancel()
        recv_task.cancel()
        try:
            await recv_task
        except asyncio.CancelledError:
            pass
