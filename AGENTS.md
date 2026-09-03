# Repository guidance

## Architecture

- Read `PLAN.md` and `docs/architecture.md` before changing component
  boundaries.
- Keep agents and tools independently executable.
- Start deterministic capabilities as tools; do not add an LLM unless the
  component needs its own reasoning loop.
- Use explicit, language-neutral CLI and JSON contracts between components.
- Preserve source provenance through tool and agent responses.
- Do not introduce bootstrap non-goals such as an orchestrator, MCP, RAG,
  persistent memory, HTTP services, or a general agent framework.

## Interfaces

- Human-facing commands should be ergonomic and readable.
- Machine mode must write only protocol output to stdout; diagnostics and logs
  belong on stderr.
- Validate structured inputs and return structured errors with a nonzero exit
  status.
- Keep model endpoints, model identifiers, credentials, and iteration limits in
  runtime configuration rather than source code.
- Never expose arbitrary shell execution as an LLM tool.

## Development workflow

- Work on a `feature/` branch in `.worktrees/<branch-name>` rather than directly
  on `master`.
- Use Nix for reproducible development, packaging, and composition.
- Use uv for Python project and dependency management once Python code is
  introduced; commit its lockfile.
- Keep prompts and schemas in versioned files rather than scattering them
  through application code.
- Add contract-focused tests without requiring live LLM or Internet access.
- Run `nix fmt -- --check flake.nix` and `nix flake check` before committing.

## Scope status

Milestone 1 is repository scaffolding only. `research-agent` and
`web-search-tool` are planned interfaces, not commands available on this branch
yet.
