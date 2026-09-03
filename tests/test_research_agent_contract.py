"""Acceptance tests for the Milestone 2 executable protocol."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from conftest import RunAgent
from jsonschema import Draft202012Validator

CONTRACT_DIR = Path(__file__).parent / "contracts" / "v0.1"


def load_schema(name: str) -> dict[str, Any]:
    with (CONTRACT_DIR / f"{name}.schema.json").open(encoding="utf-8") as stream:
        return json.load(stream)


def parse_json_stdout(stdout: str) -> Any:
    """Require stdout to contain one JSON document and no logging noise."""
    return json.loads(stdout)


def assert_valid(payload: Any, schema_name: str) -> None:
    schema = load_schema(schema_name)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)


def test_versioned_contract_schemas_are_valid() -> None:
    for name in ("request", "response", "manifest"):
        Draft202012Validator.check_schema(load_schema(name))


def test_help_is_successful_and_identifies_the_command(run_agent: RunAgent) -> None:
    result = run_agent("--help")

    assert result.returncode == 0
    assert "research-agent" in result.stdout
    assert "usage" in result.stdout.lower()
    assert result.stderr == ""


def test_manifest_matches_protocol_and_versioned_schemas(run_agent: RunAgent) -> None:
    result = run_agent("--manifest")

    assert result.returncode == 0
    assert result.stderr == ""
    manifest = parse_json_stdout(result.stdout)
    assert_valid(manifest, "manifest")
    assert manifest["protocol_version"] == "0.1"
    assert manifest["name"] == "research-agent"
    assert "research" in manifest["capabilities"]
    assert manifest["input_schema"] == load_schema("request")
    assert manifest["output_schema"] == load_schema("response")


def test_human_query_returns_readable_sections(run_agent: RunAgent) -> None:
    result = run_agent("What are the security properties of Nix sandboxing?")

    assert result.returncode == 0
    assert result.stderr == ""
    for heading in ("Summary", "Findings", "Sources"):
        assert re.search(rf"(?m)^{heading}\s*$", result.stdout)


def test_json_query_from_stdin_returns_structured_result(run_agent: RunAgent) -> None:
    request = {"query": "What are the security properties of Nix sandboxing?"}
    assert_valid(request, "request")

    result = run_agent("--json", stdin=json.dumps(request))

    assert result.returncode == 0
    payload = parse_json_stdout(result.stdout)
    assert_valid(payload, "response")
    assert payload["status"] == "success"
    assert result.stderr == ""


@pytest.mark.parametrize(
    ("stdin", "expected_code"),
    [
        ("not JSON", "invalid_json"),
        ("{}", "invalid_request"),
        ('{"query":""}', "invalid_request"),
        ('{"query":42}', "invalid_request"),
        ('{"query":"valid","unexpected":true}', "invalid_request"),
    ],
)
def test_invalid_json_requests_return_structured_errors(
    run_agent: RunAgent,
    stdin: str,
    expected_code: str,
) -> None:
    result = run_agent("--json", stdin=stdin)

    assert result.returncode != 0
    payload = parse_json_stdout(result.stdout)
    assert_valid(payload, "response")
    assert payload["status"] == "error"
    assert payload["error"]["code"] == expected_code
    assert result.stderr == ""


def test_json_mode_wraps_cli_parse_errors(run_agent: RunAgent) -> None:
    result = run_agent("--json", "--not-a-real-option")

    assert result.returncode != 0
    payload = parse_json_stdout(result.stdout)
    assert_valid(payload, "response")
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "invalid_arguments"
    assert result.stderr == ""


def test_missing_human_query_reports_only_to_stderr(run_agent: RunAgent) -> None:
    result = run_agent()

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr.strip()
