# Model client

Milestone 3 provides a small internal client for OpenAI-compatible chat
completion endpoints. It supports local or hosted inference without coupling
the research agent to a specific model provider.

## Configuration

All configuration is supplied at runtime:

| Variable | Required | Default | Meaning |
| --- | --- | --- | --- |
| `MODEL_ENDPOINT` | yes | none | Base API URL, including `/v1` when required |
| `MODEL_NAME` | yes | none | Model identifier sent with each request |
| `MODEL_API_KEY` | no | none | Bearer credential for authenticated endpoints |
| `MODEL_TEMPERATURE` | no | `0.0` | Sampling temperature from `0` through `2` |
| `MODEL_MAX_TOKENS` | no | omitted | Positive maximum output-token count |
| `MODEL_TIMEOUT_SECONDS` | no | `30` | Positive HTTP timeout in seconds |

Trailing slashes are removed from the endpoint. CLI configuration is not
introduced in this milestone, so there is no precedence hierarchy beyond the
environment.

For a local OpenAI-compatible server:

```console
export MODEL_ENDPOINT=http://127.0.0.1:8080/v1
export MODEL_NAME=local-model
```

For an authenticated endpoint, also resolve `MODEL_API_KEY` through the chosen
secret provider. Do not place credentials in source, Nix expressions, command
arguments, or committed environment files.

## Internal interface

```python
from research_agent.model import ModelConfig, OpenAICompatibleClient

config = ModelConfig.from_env()
client = OpenAICompatibleClient(config)
response = client.complete(
    [
        {"role": "system", "content": "Answer precisely."},
        {"role": "user", "content": "What is reproducibility?"},
    ]
)
print(response.content)
```

`complete` accepts optional OpenAI-compatible `tools` and `response_format`
values. It normalizes the first returned choice into content, tool calls,
finish reason, model name, and usage metadata.

## Errors and credentials

Expected failures raise `ModelClientError` with a stable `code`, human-readable
`message`, specific `reason`, and an optional HTTP `status_code`. Configuration,
HTTP, connection, and malformed-response failures have separate codes.

The API key is excluded from `ModelConfig` representations and redacted from
transport-error text. Local endpoints work without an API key.

## Milestone boundary

The client is tested through an in-process fake server and is not yet invoked
by the `research-agent` CLI. It contains no reasoning loop, tool execution, or
research synthesis. Those behaviors belong to later milestones.
