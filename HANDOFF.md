# Handoff

## Current status

Milestone 1 is complete on `feature/milestone-1-foundation` in:

```text
/home/derek/projects/ai-agents/.worktrees/feature/milestone-1-foundation
```

The branch is based on `master`, tracks
`origin/feature/milestone-1-foundation`, and contains the Nix/uv repository
foundation plus a test-first specification derived from `PLAN.md`.

The latest implementation checkpoint before this handoff is `c3566f1`.

## Last completed step

- Added a pinned Nix development shell and `flake.lock`.
- Added the initial agent/tool directory boundaries and architecture docs.
- Added a locked uv environment with pytest and Ruff.
- Added 26 offline acceptance tests covering Milestones 1 through 7.
- Added local fake HTTP infrastructure for model and search-provider tests.
- Kept Milestone 8 unspecified because the plan requires selecting the second
  tool only after dogfooding the first workflow.

Milestone 1 is green. Later milestone suites intentionally begin red and should
be implemented one milestone at a time.

## Next step

Implement Milestone 2: the deterministic `research-agent` protocol and Nix
package. Do not add an LLM, web search, tool invocation, or a reasoning loop.

Start by observing the red tests:

```console
make test-milestone-2
```

Implement only enough to satisfy
`tests/test_milestone2_agent_protocol.py`:

- `research-agent --help`
- `research-agent --manifest`
- human output with Summary, Findings, and Sources sections
- JSON requests over stdin with protocol-only stdout
- deterministic placeholder success responses
- structured `{code, message, reason}` errors and nonzero status
- a `packages.<system>.research-agent` Nix package

Keep request/response schemas and protocol documentation in versioned files as
required by `PLAN.md` and `AGENTS.md`.

When Milestone 2 is green, update this handoff and commit that step before
starting Milestone 3.

## Test workflow

```console
# Current green milestone
make test-current

# All acceptance tests; expected to remain red until later milestones
make test

# Static and Nix checks
uv sync --frozen
uv run --frozen ruff check .
uv run --frozen pytest --collect-only -q
nix fmt -- --check flake.nix
nix flake check --print-build-logs
```

Acceptance tests discover executables from `RESEARCH_AGENT_BIN` and
`WEB_SEARCH_TOOL_BIN`, falling back to `PATH`. See `tests/README.md` for the
coverage map.

## Verification at handoff

- `uv sync --frozen`: passed
- `uv run --frozen ruff check .`: passed
- `uv run --frozen pytest --collect-only -q`: 26 tests collected
- `uv run --frozen pytest -m milestone1 -q`: 5 passed
- `nix fmt -- --check flake.nix`: passed
- `nix flake check --print-build-logs`: passed
- `nix develop` toolchain smoke test: passed

## Open risks and assumptions

- The tests intentionally define observable contracts before implementation.
  If a contract must change, update `docs/protocol.md`, schemas, tests, and this
  handoff together; do not weaken a test only to fit an implementation.
- Milestone 3 tests target `research_agent.model` directly so the Milestone 2
  CLI remains deterministic. The expected minimal API is visible in
  `tests/test_milestone3_model_client.py`.
- Milestone 5 and 6 use local scripted OpenAI-compatible responses. They must
  remain offline and must not require real credentials.
- Nix evaluates the Git-visible tree. Stage newly added files before debugging
  misleading "path is not tracked" evaluation failures.
- In restricted environments, set `UV_CACHE_DIR` to a writable temporary path
  if the default user cache is read-only.
