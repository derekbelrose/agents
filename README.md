# AI Agents

AI Agents is a learning-focused toolkit for building small, independently
executable agents and tools with reproducible Nix environments.

The project is intentionally starting with a narrow architecture:

- Nix packages and composes components.
- Tools provide deterministic capabilities.
- Agents decide when and how to use those capabilities.
- Humans, agents, and future orchestrators share the same CLI and JSON
  interfaces.

See [PLAN.md](PLAN.md) for the complete bootstrap plan and
[docs/architecture.md](docs/architecture.md) for the initial component
boundaries.

## Current status

Milestone 2 provides the executable and JSON protocol for `research-agent`.
Responses are deterministic placeholders until model and tool integration are
introduced in later milestones. `web-search-tool` is not implemented yet.

The planned first usable path is:

```text
human or program -> research-agent -> web-search-tool -> external search API
```

## Prerequisites

- Git
- Nix with flakes enabled

No globally installed Python packages are required.

## Enter the development environment

```console
nix develop
```

The shell provides Python, uv, jq, and the Nix formatter used by the project.
uv installs the locked Python development dependencies into `.venv`.

```console
uv sync --frozen
```

## Run the protocol milestone

```console
uv run --frozen research-agent --help
uv run --frozen research-agent --manifest
uv run --frozen research-agent "What are the security properties of Nix?"
echo '{"query":"What are the security properties of Nix?"}' \
  | uv run --frozen research-agent --json
```

The Nix-packaged executable exposes the same interface:

```console
nix run .#research-agent -- --manifest
```

See [docs/protocol.md](docs/protocol.md) for the complete protocol behavior.
The internal model client and runtime configuration are documented in
[docs/model-client.md](docs/model-client.md).

## Verify the repository

```console
nix flake check
nix fmt -- --check flake.nix
uv run --frozen ruff check .
uv run --frozen pytest --collect-only -q
```

`nix flake check` builds `research-agent` and runs the complete executable
contract suite against the Nix package.

## Repository layout

```text
agents/             reasoning components
  research/         future research-agent
tools/              deterministic capabilities
docs/               architecture and protocol documentation
tests/              cross-component and contract tests
flake.nix           reproducible checks and development shell
PLAN.md             bootstrap scope and milestones
AGENTS.md           repository guidance for coding agents
```

## Development workflow

Create implementation work on a `feature/` branch in a Git worktree under
`.worktrees/`. Keep commits focused, update documentation with observable
behavior, and run the frozen uv and Nix checks before sharing a branch. Add
Python dependencies with `uv add` or `uv add --dev`, and commit `uv.lock`.
