import json

import pytest
from conftest import nix_package_eval, run_cli, scripted_server


@pytest.mark.milestone4
def test_search_tool_exposes_help_and_manifest(web_search_tool: str) -> None:
    help_result = run_cli(web_search_tool, "--help")
    manifest_result = run_cli(web_search_tool, "--manifest")
    manifest = json.loads(manifest_result.stdout)
    assert help_result.returncode == 0
    assert "--json" in help_result.stdout
    assert manifest_result.returncode == 0
    assert manifest["name"] == "web-search-tool"
    assert manifest["capabilities"] == ["web-search"]


@pytest.mark.milestone4
def test_search_tool_normalizes_results_and_preserves_provenance(web_search_tool: str) -> None:
    provider_response = {
        "web": {
            "results": [
                {
                    "title": "Example source",
                    "url": "https://example.test/source",
                    "description": "Evidence snippet",
                }
            ]
        }
    }
    with scripted_server([provider_response]) as server:
        endpoint = f"http://127.0.0.1:{server.server_port}/search"
        result = run_cli(
            web_search_tool,
            "--json",
            stdin=json.dumps({"query": "reproducible builds"}),
            env={"WEB_SEARCH_ENDPOINT": endpoint, "BRAVE_API_KEY": "test-secret"},
        )

    response = json.loads(result.stdout)
    assert result.returncode == 0
    assert response["status"] == "success"
    source = response["result"]["results"][0]
    assert source.keys() >= {"title", "location", "snippet", "retrieved_at"}
    assert source["location"] == "https://example.test/source"
    assert "test-secret" not in result.stdout
    assert "test-secret" not in result.stderr


@pytest.mark.milestone4
def test_search_tool_rejects_invalid_structured_input(web_search_tool: str) -> None:
    result = run_cli(web_search_tool, "--json", stdin="{}")
    response = json.loads(result.stdout)
    assert result.returncode != 0
    assert response["status"] == "error"
    assert response["error"].keys() >= {"code", "message", "reason"}


@pytest.mark.milestone4
def test_nix_exposes_web_search_tool_package() -> None:
    result = nix_package_eval("web-search-tool")
    assert result.returncode == 0, result.stderr
