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

Milestone 1 establishes the repository, development shell, directory layout,
and architecture documentation. It does not yet implement `research-agent` or
`web-search-tool`.

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

## Verify the repository

```console
nix flake check
nix fmt -- --check flake.nix
uv run --frozen ruff check .
uv run --frozen pytest --collect-only -q
```

`nix flake check` validates the repository structure and contract-test
collection. The executable contract tests remain intentionally red until
Milestone 2 is implemented.

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
