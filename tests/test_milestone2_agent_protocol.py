import json

import pytest
from conftest import nix_package_eval, run_cli


@pytest.mark.milestone2
def test_help_is_successful_and_documents_interfaces(research_agent: str) -> None:
    result = run_cli(research_agent, "--help")
    assert result.returncode == 0
    assert "--json" in result.stdout
    assert "--manifest" in result.stdout


@pytest.mark.milestone2
def test_manifest_is_minimal_machine_readable_contract(research_agent: str) -> None:
    result = run_cli(research_agent, "--manifest")
    manifest = json.loads(result.stdout)
    assert result.returncode == 0
    assert result.stderr == ""
    assert manifest.keys() >= {
        "protocol_version",
        "name",
        "description",
        "version",
        "input_schema",
        "output_schema",
        "capabilities",
    }
    assert manifest["name"] == "research-agent"
    assert manifest["protocol_version"] == "0.1"
    assert manifest["capabilities"] == ["research"]


@pytest.mark.milestone2
def test_json_request_returns_deterministic_placeholder(research_agent: str) -> None:
    request = json.dumps({"query": "What is a reproducible build?"})
    result = run_cli(research_agent, "--json", stdin=request)
    response = json.loads(result.stdout)
    assert result.returncode == 0
    assert response["status"] == "success"
    assert response["result"].keys() >= {"summary", "findings", "sources", "confidence"}
    assert isinstance(response["result"]["findings"], list)
    assert isinstance(response["result"]["sources"], list)


@pytest.mark.milestone2
@pytest.mark.parametrize("raw_request", ["not json", "{}", '{"query": ""}'])
def test_bad_json_requests_return_structured_errors(
    research_agent: str, raw_request: str
) -> None:
    result = run_cli(research_agent, "--json", stdin=raw_request)
    response = json.loads(result.stdout)
    assert result.returncode != 0
    assert response["status"] == "error"
    assert response["error"].keys() >= {"code", "message", "reason"}


@pytest.mark.milestone2
def test_human_output_has_readable_sections(research_agent: str) -> None:
    result = run_cli(research_agent, "What is a reproducible build?")
    assert result.returncode == 0
    assert all(heading in result.stdout for heading in ("Summary", "Findings", "Sources"))


@pytest.mark.milestone2
def test_nix_exposes_research_agent_package() -> None:
    result = nix_package_eval("research-agent")
    assert result.returncode == 0, result.stderr
