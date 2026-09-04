import json

import pytest
from conftest import run_cli, scripted_server


def structured_completion(research: dict[str, object]) -> dict[str, object]:
    return {
        "id": "structured-test",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": json.dumps(research)},
                "finish_reason": "stop",
            }
        ],
    }


@pytest.mark.milestone6
def test_research_response_has_traceable_findings(research_agent: str) -> None:
    research_fixture = {
        "summary": "A supported summary",
        "confidence": 0.8,
        "sources": [
            {
                "id": "source-1",
                "title": "Example",
                "location": "https://example.test/source",
                "retrieved_at": "2026-01-01T00:00:00Z",
            }
        ],
        "findings": [{"text": "Supported finding", "source_ids": ["source-1"]}],
    }
    with scripted_server([structured_completion(research_fixture)]) as server:
        result = run_cli(
            research_agent,
            "--json",
            stdin=json.dumps({"query": "Research a topic with sources"}),
            env={
                "MODEL_ENDPOINT": f"http://127.0.0.1:{server.server_port}/v1",
                "MODEL_NAME": "test-model",
            },
        )
    response = json.loads(result.stdout)
    assert result.returncode == 0
    research = response["result"]
    assert isinstance(research["summary"], str) and research["summary"]
    assert isinstance(research["confidence"], (int, float))
    assert 0 <= research["confidence"] <= 1
    assert research["findings"]
    assert research["sources"]

    source_ids = {source["id"] for source in research["sources"]}
    for source in research["sources"]:
        assert source.keys() >= {"id", "title", "location", "retrieved_at"}
    for finding in research["findings"]:
        assert finding.keys() >= {"text", "source_ids"}
        assert finding["source_ids"]
        assert set(finding["source_ids"]) <= source_ids


@pytest.mark.milestone6
def test_research_response_exposes_uncertainty(research_agent: str) -> None:
    research_fixture = {
        "summary": "Evidence is incomplete",
        "confidence": 0.2,
        "sources": [],
        "findings": [],
    }
    with scripted_server([structured_completion(research_fixture)]) as server:
        result = run_cli(
            research_agent,
            "--json",
            stdin=json.dumps({"query": "Research an uncertain topic"}),
            env={
                "MODEL_ENDPOINT": f"http://127.0.0.1:{server.server_port}/v1",
                "MODEL_NAME": "test-model",
            },
        )
    response = json.loads(result.stdout)
    assert "confidence" in response["result"]
