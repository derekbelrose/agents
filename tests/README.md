# Test-first roadmap

The tests are executable acceptance criteria derived from `PLAN.md`. They test
observable contracts and avoid live LLM and Internet dependencies.

Run the currently implemented milestone:

```console
make test-current
```

Start a later milestone in the red state:

```console
make test-milestone-2
```

Run the complete target specification (expected to fail until Milestone 7):

```console
make test
```

## Coverage map

| Milestone | Tests establish |
| --- | --- |
| 1 | Required repository layout and documentation |
| 2 | Help, manifest, human output, JSON input/output, structured errors, clean stdout |
| 3 | Runtime model configuration and an OpenAI-compatible round trip |
| 4 | Independent search CLI, normalized results, provenance, structured errors |
| 5 | Tool registration/invocation and a hard maximum iteration count |
| 6 | Findings-to-sources integrity, confidence, and uncertainty |
| 7 | Exact Codex-facing human and machine invocation guidance |

Milestone 8 deliberately has no test yet. The plan requires choosing the second
tool only after dogfooding reveals which capability is useful. Writing a test
before that decision would manufacture a component boundary the plan leaves
open.

## Executable discovery

Acceptance tests use `RESEARCH_AGENT_BIN` and `WEB_SEARCH_TOOL_BIN` when set.
Otherwise they look for `research-agent` and `web-search-tool` on `PATH`. A
missing executable is a test failure, not a skip, so an unimplemented milestone
begins red.

The model and search-provider tests start local HTTP fakes. No credentials,
Internet access, or live models are required.
