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

The shell provides Python, uv, pytest, Ruff, jq, and the Nix formatter used by
the project.

## Verify the repository

```console
nix flake check
nix fmt -- --check flake.nix
```

`nix flake check` currently validates the Milestone 1 repository structure.
Contract and implementation tests will be added alongside later milestones.

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
behavior, and run `nix flake check` before sharing a branch.
