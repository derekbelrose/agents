# Nix-Packaged Agent Toolkit

A small learning project for building independently executable AI agents and
deterministic tools with explicit CLI/JSON contracts and reproducible Nix
packages.

The project intentionally starts with concrete components. It is not a general
agent framework.

## Current status

Milestone 1 establishes the repository foundation:

- a reproducible Nix development shell;
- the initial agent and tool directory boundaries;
- architecture documentation; and
- automated checks for the repository structure.

The `research-agent` and `web-search-tool` executables are planned but are not
implemented in this milestone.

## Development

Enter the development environment:

```console
nix develop
```

Run all repository checks:

```console
nix flake check
```

Check formatting:

```console
nix fmt -- --check flake.nix
```

Run the Milestone 1 structural test directly:

```console
bash tests/milestone1.sh
```

## Repository layout

```text
agents/research/       Research agent boundary
tools/web-search/      Web search tool boundary
docs/                  Architecture and protocol documentation
tests/                 Offline contract and repository checks
flake.nix               Nix development and check entry point
```

See [PLAN.md](PLAN.md) for the incremental roadmap and
[docs/architecture.md](docs/architecture.md) for the architectural boundaries.
