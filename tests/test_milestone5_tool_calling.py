import json
from pathlib import Path

import pytest
from conftest import run_cli, scripted_server


def completion(message: dict[str, object], finish_reason: str) -> dict[str, object]:
    return {
        "id": "test-completion",
        "object": "chat.completion",
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
    }


@pytest.mark.milestone5
def test_agent_registers_and_invokes_search_tool(
    research_agent: str, tmp_path: Path
) -> None:
    invocation = tmp_path / "invocation.json"
    fake_tool = tmp_path / "web-search-tool"
    fake_tool.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "request = json.load(sys.stdin)\n"
        "open(os.environ['INVOCATION_FILE'], 'w').write(json.dumps(request))\n"
        "json.dump({'status':'success','result':{'results':["
        "{'title':'Source','location':'https://example.test','snippet':'Evidence',"
        "'retrieved_at':'2026-01-01T00:00:00Z'}]}}, sys.stdout)\n"
    )
    fake_tool.chmod(0o755)
    tool_call = completion(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "arguments": json.dumps({"query": "reproducible builds"}),
                    },
                }
            ],
        },
        "tool_calls",
    )
    final = completion(
        {"role": "assistant", "content": "Evidence-backed response"}, "stop"
    )

    with scripted_server([tool_call, final]) as server:
        result = run_cli(
            research_agent,
            "--json",
            stdin=json.dumps({"query": "Research reproducible builds"}),
            env={
                "MODEL_ENDPOINT": f"http://127.0.0.1:{server.server_port}/v1",
                "MODEL_NAME": "test-model",
                "WEB_SEARCH_TOOL": str(fake_tool),
                "INVOCATION_FILE": str(invocation),
                "MAX_AGENT_ITERATIONS": "3",
            },
        )

    assert result.returncode == 0
    assert json.loads(invocation.read_text()) == {"query": "reproducible builds"}
    assert len(server.requests) == 2
    second_messages = server.requests[1]["body"]["messages"]
    assert any(message.get("role") == "tool" for message in second_messages)


@pytest.mark.milestone5
def test_iteration_limit_stops_repeated_tool_calls(research_agent: str) -> None:
    repeated_call = completion(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-repeat",
                    "type": "function",
                    "function": {"name": "web_search", "arguments": '{"query":"again"}'},
                }
            ],
        },
        "tool_calls",
    )
    with scripted_server([repeated_call, repeated_call, repeated_call]) as server:
        result = run_cli(
            research_agent,
            "--json",
            stdin=json.dumps({"query": "Never stop searching"}),
            env={
                "MODEL_ENDPOINT": f"http://127.0.0.1:{server.server_port}/v1",
                "MODEL_NAME": "test-model",
                "MAX_AGENT_ITERATIONS": "2",
            },
        )

    assert result.returncode != 0
    assert len(server.requests) <= 2
    response = json.loads(result.stdout)
    assert response["status"] == "error"
    assert response["error"]["code"] == "iteration_limit_exceeded"


@pytest.mark.milestone5
def test_debug_logging_is_observable_and_keeps_stdout_machine_readable(
    research_agent: str,
) -> None:
    final = completion({"role": "assistant", "content": "Final response"}, "stop")
    with scripted_server([final]) as server:
        result = run_cli(
            research_agent,
            "--json",
            "--debug",
            stdin=json.dumps({"query": "Log this request"}),
            env={
                "MODEL_ENDPOINT": f"http://127.0.0.1:{server.server_port}/v1",
                "MODEL_NAME": "test-model",
                "MODEL_API_KEY": "must-not-leak",
            },
        )

    assert result.returncode == 0
    json.loads(result.stdout)
    assert "iteration" in result.stderr.lower()
    assert "duration" in result.stderr.lower()
    assert "must-not-leak" not in result.stdout
    assert "must-not-leak" not in result.stderr
