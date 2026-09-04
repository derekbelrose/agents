import pytest
from conftest import scripted_server


@pytest.mark.milestone3
def test_model_client_uses_runtime_openai_compatible_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from research_agent.model import ModelConfig, OpenAICompatibleModelClient

    response = {
        "id": "test-completion",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Local model response"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 4, "completion_tokens": 3, "total_tokens": 7},
    }
    with scripted_server([response]) as server:
        endpoint = f"http://127.0.0.1:{server.server_port}/v1"
        monkeypatch.setenv("MODEL_ENDPOINT", endpoint)
        monkeypatch.setenv("MODEL_NAME", "test-model")
        monkeypatch.setenv("MODEL_API_KEY", "test-secret")
        client = OpenAICompatibleModelClient(ModelConfig.from_env())
        result = client.complete([{"role": "user", "content": "Use the model"}])

    assert result.content == "Local model response"
    assert result.metadata["usage"]["total_tokens"] == 7
    assert len(server.requests) == 1
    request = server.requests[0]
    assert request["path"] == "/v1/chat/completions"
    assert request["body"]["model"] == "test-model"
    assert request["headers"]["Authorization"] == "Bearer test-secret"


@pytest.mark.milestone3
def test_missing_model_configuration_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    from research_agent.model import ConfigurationError, ModelConfig

    monkeypatch.delenv("MODEL_ENDPOINT", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    with pytest.raises(ConfigurationError):
        ModelConfig.from_env()
