# Tests

This directory holds cross-component and executable-contract tests. Normal
checks remain deterministic and do not require live LLM or Internet access.

## Milestone 2 contract tests

The tests in `test_research_agent_contract.py` treat `research-agent` as an
opaque executable. They define protocol version `0.1` without importing any
agent implementation.

By default, the suite resolves `research-agent` from `PATH`. Override the
executable under test with `RESEARCH_AGENT_BIN`:

```console
uv sync --frozen
RESEARCH_AGENT_BIN=/path/to/research-agent uv run --frozen pytest -q
```

Until Milestone 2 is implemented, the suite is expected to fail with a clear
message that `research-agent` could not be found. Verify the tests themselves
without running the absent implementation:

```console
uv run --frozen pytest --collect-only -q
```

Collection is also enforced by `nix flake check`.

## Milestone 3 model-client tests

`test_model_client.py` defines the internal model-client contract before its
implementation. The tests use an in-process fake OpenAI-compatible HTTP server;
they require no network access, model weights, or credentials.

The suite covers external runtime configuration, optional bearer
authentication, generation parameters, messages, tool definitions, structured
response formats, normalized responses, malformed responses, transport errors,
and credential-safe representations.

Until the Milestone 3 client exists, the model-client tests are expected to
stop at a clear `research_agent.model is not implemented` fixture failure.

## Milestone 4 web-search tests

`test_web_search.py` defines the external executable contract for the first
deterministic tool. It drives the future `web-search` process against an
in-process fake Brave API, so the suite requires no live network or credential.

The tests cover help and manifest discovery, human and JSON interfaces,
versioned schemas, SecretSpec declaration, Brave request construction,
normalized results and provenance, configuration, structured errors, and
credential-safe output.

Until Milestone 4 is implemented, the executable tests stop at a clear missing
`web-search` fixture failure and the SecretSpec test fails because its
declaration does not exist. Collection remains enforced by `nix flake check`.
