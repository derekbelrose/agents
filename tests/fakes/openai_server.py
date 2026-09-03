"""In-process fake for the OpenAI-compatible chat completions endpoint."""

from __future__ import annotations

import json
import threading
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


@dataclass(frozen=True)
class RecordedRequest:
    path: str
    headers: dict[str, str]
    payload: Any


@dataclass(frozen=True)
class QueuedResponse:
    status: int
    body: bytes
    content_type: str


class FakeOpenAIServer(ThreadingHTTPServer):
    """Record requests and serve queued deterministic responses."""

    requests: list[RecordedRequest]
    responses: deque[QueuedResponse]

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _RequestHandler)
        self.requests = []
        self.responses = deque()

    @property
    def endpoint(self) -> str:
        host, port = self.server_address
        return f"http://{host}:{port}/v1"

    def enqueue_json(self, payload: Any, status: int = 200) -> None:
        self.responses.append(
            QueuedResponse(
                status=status,
                body=json.dumps(payload).encode(),
                content_type="application/json",
            )
        )

    def enqueue_text(self, body: str, status: int = 200) -> None:
        self.responses.append(
            QueuedResponse(
                status=status,
                body=body.encode(),
                content_type="text/plain",
            )
        )


class _RequestHandler(BaseHTTPRequestHandler):
    server: FakeOpenAIServer

    def do_POST(self) -> None:  # noqa: N802 - method name is defined by stdlib
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = body.decode(errors="replace")

        self.server.requests.append(
            RecordedRequest(
                path=self.path,
                headers={key.lower(): value for key, value in self.headers.items()},
                payload=payload,
            )
        )
        response = self.server.responses.popleft()
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        self.wfile.write(response.body)

    def log_message(self, format: str, *args: object) -> None:
        return


@contextmanager
def running_openai_server() -> Iterator[FakeOpenAIServer]:
    server = FakeOpenAIServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
