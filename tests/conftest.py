from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


def executable(env_name: str, command: str) -> str:
    candidate = os.environ.get(env_name) or shutil.which(command)
    assert candidate is not None, f"{command} is not implemented or not on PATH"
    return candidate


def run_cli(
    executable_path: str,
    *args: str,
    stdin: str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    return subprocess.run(
        [executable_path, *args],
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
        env=process_env,
    )


def nix_package_eval(package: str) -> subprocess.CompletedProcess[str]:
    system = subprocess.run(
        ["nix", "eval", "--impure", "--raw", "--expr", "builtins.currentSystem"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    with tempfile.TemporaryDirectory(prefix="ai-agents-nix-cache-") as cache:
        env = os.environ.copy()
        env["XDG_CACHE_HOME"] = cache
        return subprocess.run(
            ["nix", "eval", "--raw", f".#packages.{system}.{package}.name"],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )


@pytest.fixture
def research_agent() -> str:
    return executable("RESEARCH_AGENT_BIN", "research-agent")


@pytest.fixture
def web_search_tool() -> str:
    return executable("WEB_SEARCH_TOOL_BIN", "web-search-tool")


class ScriptedServer(ThreadingHTTPServer):
    script: list[dict[str, Any]]
    requests: list[dict[str, Any]]


class ScriptedHandler(BaseHTTPRequestHandler):
    server: ScriptedServer

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length))
        self.server.requests.append(
            {"path": self.path, "headers": dict(self.headers), "body": body}
        )
        response = self.server.script.pop(0)
        payload = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _format: str, *args: object) -> None:
        pass


@contextmanager
def scripted_server(script: list[dict[str, Any]]) -> Iterator[ScriptedServer]:
    server = ScriptedServer(("127.0.0.1", 0), ScriptedHandler)
    server.script = list(script)
    server.requests = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
