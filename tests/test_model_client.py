"""Contract tests for the Milestone 3 OpenAI-compatible model client."""

from __future__ import annotations

from types import ModuleType
from typing import Any

import pytest
from fakes.openai_server import FakeOpenAIServer, running_openai_server


@pytest.fixture(scope="module")
def model_api() -> ModuleType:
    """Load the future implementation only when the tests execute."""
    try:
        from research_agent import model
    except ImportError:
        pytest.fail(
            "research_agent.model is not implemented. "
            "Add the Milestone 3 model client to satisfy this contract."
        )
    return model


@pytest.fixture
def openai_server() -> Any:
    with running_openai_server() as server:
        yield server


def completion_payload(
    *,
    content: str | None = "A deterministic response.",
    tool_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": "tool_calls" if tool_calls else "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 7,
            "completion_tokens": 3,
            "total_tokens": 10,
        },
    }


def required_environment(monkeypatch: pytest.MonkeyPatch, endpoint: str) -> None:
    monkeypatch.setenv("MODEL_ENDPOINT", endpoint)
    monkeypatch.setenv("MODEL_NAME", "test-model")
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_TEMPERATURE", raising=False)
    monkeypatch.delenv("MODEL_MAX_TOKENS", raising=False)
    monkeypatch.delenv("MODEL_TIMEOUT_SECONDS", raising=False)


def test_configuration_is_loaded_from_environment(
    model_api: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MODEL_ENDPOINT", "http://127.0.0.1:8080/v1/")
    monkeypatch.setenv("MODEL_NAME", "local-model")
    monkeypatch.setenv("MODEL_API_KEY", "top-secret")
    monkeypatch.setenv("MODEL_TEMPERATURE", "0.25")
    monkeypatch.setenv("MODEL_MAX_TOKENS", "512")
    monkeypatch.setenv("MODEL_TIMEOUT_SECONDS", "4.5")

    config = model_api.ModelConfig.from_env()

    assert config.endpoint == "http://127.0.0.1:8080/v1"
    assert config.model == "local-model"
    assert config.api_key == "top-secret"
    assert config.temperature == 0.25
    assert config.max_tokens == 512
    assert config.timeout_seconds == 4.5


@pytest.mark.parametrize("missing", ["MODEL_ENDPOINT", "MODEL_NAME"])
def test_required_configuration_is_validated(
    model_api: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
) -> None:
    required_environment(monkeypatch, "http://127.0.0.1:8080/v1")
    monkeypatch.delenv(missing)

    with pytest.raises(model_api.ModelClientError) as captured:
        model_api.ModelConfig.from_env()

    assert captured.value.code == "invalid_model_configuration"
    assert missing in captured.value.reason


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("MODEL_ENDPOINT", "ftp://models.invalid/v1"),
        ("MODEL_TEMPERATURE", "not-a-number"),
        ("MODEL_TEMPERATURE", "2.1"),
        ("MODEL_MAX_TOKENS", "0"),
        ("MODEL_TIMEOUT_SECONDS", "-1"),
    ],
)
def test_invalid_configuration_is_rejected(
    model_api: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    variable: str,
    value: str,
) -> None:
    required_environment(monkeypatch, "http://127.0.0.1:8080/v1")
    monkeypatch.setenv(variable, value)

    with pytest.raises(model_api.ModelClientError) as captured:
        model_api.ModelConfig.from_env()

    assert captured.value.code == "invalid_model_configuration"
    assert variable in captured.value.reason


def test_api_key_is_redacted_from_configuration_representation(
    model_api: ModuleType,
) -> None:
    config = model_api.ModelConfig(
        endpoint="https://models.example/v1",
        model="test-model",
        api_key="credential-must-not-leak",
    )

    assert "credential-must-not-leak" not in repr(config)


def test_chat_completion_sends_runtime_configuration_and_normalizes_response(
    model_api: ModuleType,
    openai_server: FakeOpenAIServer,
) -> None:
    openai_server.enqueue_json(completion_payload())
    config = model_api.ModelConfig(
        endpoint=openai_server.endpoint,
        model="test-model",
        api_key="test-credential",
        temperature=0.3,
        max_tokens=256,
        timeout_seconds=2,
    )
    messages = [
        {"role": "system", "content": "Answer precisely."},
        {"role": "user", "content": "What is reproducibility?"},
    ]

    response = model_api.OpenAICompatibleClient(config).complete(messages)

    assert len(openai_server.requests) == 1
    request = openai_server.requests[0]
    assert request.path == "/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer test-credential"
    assert request.payload == {
        "model": "test-model",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 256,
    }
    assert response.content == "A deterministic response."
    assert response.tool_calls == []
    assert response.finish_reason == "stop"
    assert response.model == "test-model"
    assert response.usage == {
        "prompt_tokens": 7,
        "completion_tokens": 3,
        "total_tokens": 10,
    }


def test_local_endpoint_does_not_require_authentication(
    model_api: ModuleType,
    openai_server: FakeOpenAIServer,
) -> None:
    openai_server.enqueue_json(completion_payload())
    config = model_api.ModelConfig(
        endpoint=openai_server.endpoint,
        model="test-model",
    )

    model_api.OpenAICompatibleClient(config).complete(
        [{"role": "user", "content": "Hello"}]
    )

    request = openai_server.requests[0]
    assert "authorization" not in request.headers
    assert "max_tokens" not in request.payload
    assert request.payload["temperature"] == 0.0


def test_tool_definitions_are_forwarded_and_tool_calls_are_normalized(
    model_api: ModuleType,
    openai_server: FakeOpenAIServer,
) -> None:
    tool_calls = [
        {
            "id": "call_123",
            "type": "function",
            "function": {"name": "web_search", "arguments": '{"query":"Nix"}'},
        }
    ]
    openai_server.enqueue_json(completion_payload(content=None, tool_calls=tool_calls))
    config = model_api.ModelConfig(
        endpoint=openai_server.endpoint,
        model="test-model",
    )
    tools = [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        }
    ]

    response = model_api.OpenAICompatibleClient(config).complete(
        [{"role": "user", "content": "Research Nix"}],
        tools=tools,
    )

    assert openai_server.requests[0].payload["tools"] == tools
    assert response.content is None
    assert response.tool_calls == tool_calls
    assert response.finish_reason == "tool_calls"


def test_structured_response_format_is_forwarded(
    model_api: ModuleType,
    openai_server: FakeOpenAIServer,
) -> None:
    openai_server.enqueue_json(completion_payload(content='{"answer":"yes"}'))
    config = model_api.ModelConfig(
        endpoint=openai_server.endpoint,
        model="test-model",
    )
    response_format = {"type": "json_object"}

    response = model_api.OpenAICompatibleClient(config).complete(
        [{"role": "user", "content": "Return JSON"}],
        response_format=response_format,
    )

    assert openai_server.requests[0].payload["response_format"] == response_format
    assert response.content == '{"answer":"yes"}'


def test_http_error_is_structured_and_does_not_leak_credentials(
    model_api: ModuleType,
    openai_server: FakeOpenAIServer,
) -> None:
    openai_server.enqueue_json(
        {"error": {"message": "Access denied"}},
        status=401,
    )
    secret = "credential-must-not-leak"
    config = model_api.ModelConfig(
        endpoint=openai_server.endpoint,
        model="test-model",
        api_key=secret,
    )

    with pytest.raises(model_api.ModelClientError) as captured:
        model_api.OpenAICompatibleClient(config).complete(
            [{"role": "user", "content": "Hello"}]
        )

    error = captured.value
    assert error.code == "model_http_error"
    assert error.status_code == 401
    assert secret not in str(error)
    assert secret not in repr(error)


@pytest.mark.parametrize(
    "payload",
    [
        "not JSON",
        '{"choices":[]}',
        '{"choices":[{"message":{}}]}',
    ],
)
def test_malformed_responses_raise_a_structured_error(
    model_api: ModuleType,
    openai_server: FakeOpenAIServer,
    payload: str,
) -> None:
    openai_server.enqueue_text(payload)
    config = model_api.ModelConfig(
        endpoint=openai_server.endpoint,
        model="test-model",
    )

    with pytest.raises(model_api.ModelClientError) as captured:
        model_api.OpenAICompatibleClient(config).complete(
            [{"role": "user", "content": "Hello"}]
        )

    assert captured.value.code == "invalid_model_response"


def test_connection_failure_is_wrapped(model_api: ModuleType) -> None:
    config = model_api.ModelConfig(
        endpoint="http://127.0.0.1:1/v1",
        model="test-model",
        timeout_seconds=0.1,
    )

    with pytest.raises(model_api.ModelClientError) as captured:
        model_api.OpenAICompatibleClient(config).complete(
            [{"role": "user", "content": "Hello"}]
        )

    assert captured.value.code == "model_connection_error"
