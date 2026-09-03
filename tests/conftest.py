"""Black-box process fixture for the future research-agent executable."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from collections.abc import Callable

import pytest

RunAgent = Callable[..., subprocess.CompletedProcess[str]]


@pytest.fixture(scope="session")
def research_agent_command() -> list[str]:
    """Resolve the executable without importing implementation code."""
    configured = os.environ.get("RESEARCH_AGENT_BIN", "research-agent")
    command = shlex.split(configured)
    if not command:
        pytest.fail("RESEARCH_AGENT_BIN must contain an executable command")

    executable = command[0]
    resolved = shutil.which(executable)
    if resolved is None:
        pytest.fail(
            f"research-agent executable not found: {executable!r}. "
            "Implement Milestone 2 or set RESEARCH_AGENT_BIN to the executable "
            "under test."
        )
    command[0] = resolved
    return command


@pytest.fixture
def run_agent(research_agent_command: list[str]) -> RunAgent:
    """Run the agent with isolated, captured text streams."""

    def run(
        *arguments: str,
        stdin: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*research_agent_command, *arguments],
            input=stdin,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )

    return run
