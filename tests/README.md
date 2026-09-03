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
RESEARCH_AGENT_BIN=/path/to/research-agent pytest -q
```

Until Milestone 2 is implemented, the suite is expected to fail with a clear
message that `research-agent` could not be found. Test collection itself must
pass and is enforced by `nix flake check`.
