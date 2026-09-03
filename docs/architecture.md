# Architecture

## Purpose

This project explores the smallest useful boundary between independently
executable AI agents and the deterministic tools they use. The initial target
is one research agent using one web-search tool, with Nix providing reproducible
packaging and composition.

## Component model

```text
                         shared executable contracts
                                      |
                   +------------------+------------------+
                   |                                     |
             research-agent                       web-search-tool
          owns a reasoning loop                 owns one capability
          chooses when to search                performs no synthesis
          synthesizes evidence                  contains no LLM
                   |                                     |
                   +-------------- invokes -------------+
```

Each component must remain directly usable by a human or another program. A
future orchestrator should call the same executable and JSON interfaces rather
than relying on an internal-only API.

## Responsibilities

### Nix

- Provides development environments, packages, applications, and checks.
- Composes an agent with the exact tools it is intended to invoke.
- Does not implement the reasoning loop or imply runtime security isolation.

### Agents

- Interpret a goal and decide which registered capabilities to use.
- Own the bounded LLM reasoning and tool-calling loop.
- Validate tool arguments and preserve evidence provenance.
- Produce both human-readable and structured results.

### Tools

- Perform narrow capabilities through explicit, validated inputs.
- Produce normalized output without deciding the user's overall objective.
- Remain independently executable and replaceable behind their contract.
- Do not contain an LLM unless autonomous reasoning becomes necessary.

## Executable boundary

Every agent and independently useful tool will expose:

- `--help` for human discovery.
- `--manifest` for machine-readable identity and schemas.
- A human-friendly direct CLI.
- `--json` for structured request and response data.

Machine-readable stdout is reserved for protocol data. Diagnostics, logs, and
debug traces go to stderr. Expected failures return structured errors and a
nonzero status.

The boundary is successful if a component can be reimplemented in another
language without requiring changes from its consumers.

## Configuration and secrets

Endpoints, model identifiers, credentials, generation settings, and iteration
limits are runtime configuration. They are not compiled into packages or
embedded in source. Secret values must not appear in logs, command arguments,
manifests, or output.

## Provenance

Retrieval tools retain source titles, locations, and retrieval metadata. Agents
carry those identities into findings so synthesis does not sever evidence from
its origin. The first version needs traceability, not an elaborate citation
standard.

## Security boundary

An agent may invoke only explicitly registered tools with validated arguments.
It must not receive a generic shell-execution tool. Nix dependency composition
controls what is packaged, but it is not by itself a runtime sandbox.

## Initial repository layout

- `agents/research/`: future research-agent implementation, prompts, and
  schemas.
- `tools/`: independently executable deterministic capabilities.
- `docs/`: architecture and protocol documentation.
- `tests/`: cross-component and executable-contract tests.

More abstractions should be introduced only when working implementations expose
real duplication or requirements.

## Deferred work

The bootstrap deliberately excludes orchestrators, agent-to-agent networking,
MCP, persistent state, RAG, vector databases, HTTP services, GUIs, and general
agent frameworks. `PLAN.md` is authoritative for the complete list and milestone
sequence.
