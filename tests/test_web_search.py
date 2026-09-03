"""Acceptance tests for the independently executable web-search tool."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from fakes.brave_server import FakeBraveServer, running_brave_server
from jsonschema import Draft202012Validator, FormatChecker

RunTool = Callable[..., subprocess.CompletedProcess[str]]
CONTRACT_DIR = Path(__file__).parent / "contracts" / "web-search" / "v0.1"


def load_schema(name: str) -> dict[str, Any]:
    with (CONTRACT_DIR / f"{name}.schema.json").open(encoding="utf-8") as stream:
        return json.load(stream)


def assert_valid(payload: Any, schema_name: str) -> None:
    schema = load_schema(schema_name)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)


@pytest.fixture(scope="session")
def web_search_command() -> list[str]:
    configured = os.environ.get("WEB_SEARCH_BIN", "web-search")
    command = shlex.split(configured)
    if not command:
        pytest.fail("WEB_SEARCH_BIN must contain an executable command")
    resolved = shutil.which(command[0])
    if resolved is None:
        pytest.fail(
            f"web-search executable not found: {command[0]!r}. "
            "Implement Milestone 4 or set WEB_SEARCH_BIN to the executable under test."
        )
    command[0] = resolved
    return command


@pytest.fixture
def run_tool(web_search_command: list[str]) -> RunTool:
    def run(
        *arguments: str,
        stdin: str | None = None,
        environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        process_environment = os.environ.copy()
        process_environment.pop("BRAVE_API_KEY", None)
        process_environment.pop("BRAVE_SEARCH_ENDPOINT", None)
        process_environment.pop("WEB_SEARCH_TIMEOUT", None)
        process_environment.pop("WEB_SEARCH_MAX_RESULTS", None)
        if environment:
            process_environment.update(environment)
        return subprocess.run(
            [*web_search_command, *arguments],
            input=stdin,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
            env=process_environment,
        )

    return run


@pytest.fixture
def brave_server() -> Any:
    with running_brave_server() as server:
        yield server


def successful_provider_response() -> dict[str, Any]:
    return {
        "type": "search",
        "web": {
            "results": [
                {
                    "title": "Nix sandboxing",
                    "url": "https://example.test/nix-sandboxing",
                    "description": "An explanation of isolated Nix builds.",
                    "extra_snippets": ["Provider-specific data is ignored."],
                }
            ]
        },
    }


def fake_environment(server: FakeBraveServer) -> dict[str, str]:
    return {
        "BRAVE_API_KEY": "test-credential",
        "BRAVE_SEARCH_ENDPOINT": server.endpoint,
    }


def test_versioned_web_search_schemas_are_valid() -> None:
    for name in ("request", "response", "manifest"):
        Draft202012Validator.check_schema(load_schema(name))


def test_brave_credential_is_declared_in_secretspec() -> None:
    with (Path(__file__).parents[1] / "secretspec.toml").open("rb") as stream:
        specification = tomllib.load(stream)

    assert specification["project"] == {"name": "web-search", "revision": "1.0"}
    assert specification["profiles"]["default"]["BRAVE_API_KEY"] == {
        "description": "Brave Search API credential",
        "required": True,
    }


def test_help_is_successful_and_identifies_the_tool(run_tool: RunTool) -> None:
    result = run_tool("--help")

    assert result.returncode == 0
    assert "web-search" in result.stdout
    assert "usage" in result.stdout.lower()
    assert result.stderr == ""


def test_manifest_matches_protocol_and_versioned_schemas(run_tool: RunTool) -> None:
    result = run_tool("--manifest")

    assert result.returncode == 0
    assert result.stderr == ""
    manifest = json.loads(result.stdout)
    assert_valid(manifest, "manifest")
    assert manifest["input_schema"] == load_schema("request")
    assert manifest["output_schema"] == load_schema("response")


def test_json_stdin_search_normalizes_results_and_provenance(
    run_tool: RunTool,
    brave_server: FakeBraveServer,
) -> None:
    brave_server.enqueue_json(successful_provider_response())

    result = run_tool(
        "--json",
        stdin='{"query":"Nix sandboxing"}',
        environment=fake_environment(brave_server),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert_valid(payload, "response")
    assert payload["status"] == "success"
    assert payload["result"]["query"] == "Nix sandboxing"
    assert payload["result"]["results"] == [
        {
            "title": "Nix sandboxing",
            "url": "https://example.test/nix-sandboxing",
            "snippet": "An explanation of isolated Nix builds.",
            "source": "brave-search",
        }
    ]


def test_json_positional_query_is_supported(
    run_tool: RunTool,
    brave_server: FakeBraveServer,
) -> None:
    brave_server.enqueue_json({"web": {"results": []}})

    result = run_tool(
        "--json",
        "agent tools",
        environment=fake_environment(brave_server),
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["result"]["query"] == "agent tools"
    assert payload["result"]["results"] == []


def test_human_search_prints_title_url_and_snippet(
    run_tool: RunTool,
    brave_server: FakeBraveServer,
) -> None:
    brave_server.enqueue_json(successful_provider_response())

    result = run_tool(
        "Nix sandboxing",
        environment=fake_environment(brave_server),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert "Nix sandboxing" in result.stdout
    assert "https://example.test/nix-sandboxing" in result.stdout
    assert "An explanation of isolated Nix builds." in result.stdout


def test_request_uses_brave_authentication_and_cli_result_limit(
    run_tool: RunTool,
    brave_server: FakeBraveServer,
) -> None:
    brave_server.enqueue_json({"web": {"results": []}})

    result = run_tool(
        "--json",
        "--max-results",
        "7",
        "Nix flakes",
        environment=fake_environment(brave_server),
    )

    assert result.returncode == 0
    request = brave_server.requests[0]
    parsed = urlsplit(request.path)
    assert parsed.path == "/res/v1/web/search"
    assert parse_qs(parsed.query) == {"q": ["Nix flakes"], "count": ["7"]}
    assert request.headers["x-subscription-token"] == "test-credential"
    assert request.headers["accept"] == "application/json"


@pytest.mark.parametrize(
    ("stdin", "expected_code"),
    [
        ("not JSON", "invalid_json"),
        ("{}", "invalid_request"),
        ('{"query":""}', "invalid_request"),
        ('{"query":42}', "invalid_request"),
        ('{"query":"valid","extra":true}', "invalid_request"),
    ],
)
def test_invalid_json_requests_return_structured_errors(
    run_tool: RunTool,
    stdin: str,
    expected_code: str,
) -> None:
    result = run_tool("--json", stdin=stdin)

    assert result.returncode != 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert_valid(payload, "response")
    assert payload["status"] == "error"
    assert payload["error"]["code"] == expected_code


def test_missing_api_key_is_a_structured_json_error(run_tool: RunTool) -> None:
    result = run_tool("--json", "agent tools")

    assert result.returncode != 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert_valid(payload, "response")
    assert payload["error"]["code"] == "missing_api_key"
    assert "BRAVE_API_KEY" in payload["error"]["reason"]


def test_json_mode_wraps_cli_parse_errors(run_tool: RunTool) -> None:
    result = run_tool("--json", "--not-a-real-option")

    assert result.returncode != 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert_valid(payload, "response")
    assert payload["error"]["code"] == "invalid_arguments"


def test_human_errors_are_written_only_to_stderr(run_tool: RunTool) -> None:
    result = run_tool()

    assert result.returncode != 0
    assert result.stdout == ""
    assert "Reason:" in result.stderr


@pytest.mark.parametrize(
    ("provider_response", "status", "expected_code"),
    [
        ({"error": "rate limited"}, 429, "search_http_error"),
        ("not JSON", 200, "invalid_search_response"),
        ({"unexpected": True}, 200, "invalid_search_response"),
    ],
)
def test_provider_failures_are_structured_and_secret_safe(
    run_tool: RunTool,
    brave_server: FakeBraveServer,
    provider_response: Any,
    status: int,
    expected_code: str,
) -> None:
    if isinstance(provider_response, str):
        brave_server.enqueue_text(provider_response, status=status)
    else:
        brave_server.enqueue_json(provider_response, status=status)

    result = run_tool(
        "--json",
        "agent tools",
        environment=fake_environment(brave_server),
    )

    assert result.returncode != 0
    assert result.stderr == ""
    assert "test-credential" not in result.stdout
    payload = json.loads(result.stdout)
    assert_valid(payload, "response")
    assert payload["error"]["code"] == expected_code
