# Architecture

## Purpose

This repository builds small AI agents and deterministic tools as independently
executable programs. Nix packages and composes those programs, while each
program owns its runtime behavior.

The bootstrap architecture is intentionally concrete. Shared abstractions will
only be introduced after multiple working components demonstrate a real need.

## Component boundaries

The planned bootstrap dependency graph is:

```text
human, Codex, or future orchestrator
                 |
                 v
          research-agent
                 |
                 v
         web-search-tool
```

The same executable interface is used by humans and software. There is no
orchestrator-only internal API.

### Agents

An agent contains a reasoning loop and decides which registered capabilities
are useful for a goal. The first planned agent is `research-agent`.

### Tools

A tool implements one narrow capability without deciding the user's overall
goal. The first planned tool is `web-search-tool`. It retrieves and normalizes
search results; it does not synthesize research and does not contain an LLM.

Agents and tools remain independently executable and independently testable.

## Interface boundary

Components expose an ergonomic human CLI and a language-neutral JSON protocol.
Machine-mode stdout is reserved for protocol output. Diagnostics and logs go to
stderr. Structured inputs are validated, and structured failures use a nonzero
exit status.

Detailed request, response, manifest, and error contracts will be defined in
Milestone 2 in `docs/protocol.md` and versioned schema files.

## Packaging boundary

Nix provides reproducible development environments, packages, runtime
dependencies, checks, and package composition. It does not implement agent
reasoning. A Nix dependency relationship also does not, by itself, provide
runtime security isolation.

Implementation languages are component choices. The initial implementation is
expected to use Python with uv, but neither component contracts nor composition
may assume that every executable is Python.

## Runtime configuration

Model endpoints, model identifiers, credentials, generation settings, and
iteration limits are runtime configuration. Model weights are not included in
agent packages. Prompts and schemas are versioned repository files and will be
included in their owning packages.

## Capability and security boundaries

An LLM may invoke only explicitly registered tools with validated arguments.
No component exposes arbitrary shell execution as an LLM tool. Source identity
must survive retrieval and synthesis so results can retain provenance.

## Deliberate exclusions

The bootstrap does not include an orchestrator, MCP, RAG, persistent memory,
HTTP services, distributed agents, a general agent framework, or generalized
Nix agent constructors. These remain future options rather than architectural
requirements.
