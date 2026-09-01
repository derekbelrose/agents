# Nix-Packaged Agent Toolkit: Bootstrap Plan

## Goal

Build a small, extensible system for creating independently executable AI agents and tools packaged with Nix.

The initial implementation is intended primarily as a learning project for:

* Agentic application architecture
* LLM tool calling
* Capability isolation
* Structured agent/tool interfaces
* Model abstraction
* Nix packaging
* Reproducible agent environments
* Agent composition

Do **not** build a general-purpose agent framework up front.

Build the smallest useful implementation, learn from it, and extract abstractions only when duplication or real requirements appear.

---

# Architectural Principles

## 1. Nix Is the Packaging and Composition Layer

Nix should define:

* Agent packages
* Tool packages
* Runtime dependencies
* Development environments
* Reproducible builds
* Package composition

Nix should **not** implement the agent reasoning loop.

Agent implementations may use whatever programming language is appropriate.

The initial agent may use Python, but the architecture must not assume that all agents or tools are Python programs.

---

## 2. Agents and Tools Are Independently Executable

Every agent and tool should be usable without an orchestrator.

For example:

```bash
nix run .#research-agent -- "How does Nix sandboxing work?"
```

Tools should also be independently callable where useful:

```bash
nix run .#web-search-tool -- --query "Nix sandboxing"
```

The eventual orchestrator must consume the same interfaces used by humans and other software.

Do not create a special internal API that only the orchestrator can use.

---

## 3. Agents and Tools Are Different Concepts

Use this distinction:

> Tools perform capabilities. Agents decide which capabilities need to be used to accomplish a goal.

A component should begin life as a deterministic tool unless it requires its own reasoning loop.

Example:

```text
research-agent [LLM]
    │
    ├── web-search-tool
    ├── docs-search-tool
    └── repo-search-tool
```

`web-search-tool` should not contain an LLM merely because it is used by an agent.

If a future capability becomes sufficiently complicated to require autonomous reasoning, it can later be promoted into an agent.

For example:

```text
research-agent
    │
    └── code-research-agent [LLM]
            │
            ├── repo-search-tool
            ├── source-reader-tool
            └── git-history-tool
```

Do not implement this hierarchy yet.

---

# Initial Scope

Implement:

1. A common executable interface
2. One `research-agent`
3. One simple research tool
4. Nix packaging
5. Model-provider abstraction
6. Structured JSON input/output
7. Human-friendly CLI output
8. Tests
9. Documentation for using the agent from Codex

Do **not** implement:

* A general orchestrator
* A memory agent
* Multiple research agents
* Agent-to-agent communication
* MCP
* Distributed agents
* HTTP services
* Persistent agent state
* Vector databases
* RAG infrastructure
* Agent frameworks such as LangChain or CrewAI
* A generalized `mkAgent` Nix abstraction

Those are possible future capabilities, not bootstrap requirements.

---

# Repository Structure

Start with something approximately like:

```text
.
├── flake.nix
├── flake.lock
├── README.md
├── AGENTS.md
│
├── agents/
│   └── research/
│       ├── default.nix
│       ├── src/
│       ├── prompts/
│       │   └── system.md
│       └── schemas/
│           ├── request.json
│           └── response.json
│
├── tools/
│   └── web-search/
│       ├── default.nix
│       └── src/
│
├── docs/
│   ├── architecture.md
│   └── protocol.md
│
└── tests/
```

Adjust the exact layout if the implementation language or Nix conventions suggest something cleaner.

Avoid creating abstractions merely to make the directory structure look sophisticated.

---

# Executable Agent Contract

The most important bootstrap deliverable is a simple language-independent contract.

An agent should support at least:

```bash
research-agent --help
research-agent --manifest
research-agent --json
```

It should also support ergonomic direct CLI use:

```bash
research-agent "Research question"
```

---

# Human CLI Interface

Example:

```bash
research-agent "What are the security properties of Nix build sandboxing?"
```

Output should be optimized for a human:

```text
Summary

...

Findings

...

Sources

...
```

Exact formatting is not important yet.

---

# Machine Interface

Structured requests should be accepted over stdin.

Example:

```bash
echo '{
  "query": "What are the security properties of Nix build sandboxing?"
}' | research-agent --json
```

The response should be JSON written to stdout.

Example conceptual response:

```json
{
  "status": "success",
  "result": {
    "summary": "...",
    "findings": [],
    "sources": [],
    "confidence": 0.9
  }
}
```

The exact schema should be defined explicitly in the repository and validated.

Diagnostics and logging must go to stderr so stdout remains machine-readable.

---

# Manifest Interface

The agent should expose metadata describing itself:

```bash
research-agent --manifest
```

Conceptual output:

```json
{
  "protocol_version": "0.1",
  "name": "research-agent",
  "description": "Researches questions using available information sources.",
  "version": "0.1.0",
  "input_schema": {},
  "output_schema": {},
  "capabilities": [
    "research"
  ]
}
```

Do not over-design the manifest.

It exists so future software can discover:

* What this executable is
* What it does
* What input it accepts
* What output it returns
* Which protocol version it implements

---

# Research Agent

The initial research agent should contain one LLM reasoning loop.

Conceptually:

```text
             research-agent
                    │
                    ▼
                  LLM
                    │
             decides whether
             research is needed
                    │
                    ▼
             web-search-tool
                    │
                    ▼
              search results
                    │
                    ▼
                  LLM
                    │
                    ▼
           structured response
```

Keep the reasoning loop intentionally small.

The goal is to learn how tool-calling agents work rather than reproduce an existing agent framework.

The agent should be able to:

1. Receive a research question.
2. Determine what search query or queries are useful.
3. Invoke the available search tool.
4. Inspect results.
5. Optionally perform additional searches within a conservative iteration limit.
6. Synthesize the evidence.
7. Return structured findings with source provenance.

Put an explicit maximum on tool iterations to prevent runaway loops.

---

# Research Tools

Begin with only one research capability.

For example:

```text
web-search-tool
```

Its responsibility should be narrow:

```text
query
  ↓
search
  ↓
normalized results
```

It should not perform research synthesis.

It should not decide what the user ultimately needs.

It should not contain an LLM unless there is a compelling technical reason.

Its output should preserve enough source information for the research agent to provide provenance.

Future tools might include:

```text
docs-search-tool
repo-search-tool
local-search-tool
wiki-search-tool
```

Do not implement them during bootstrap unless needed to prove the interface.

---

# Model Interface

Do not tightly couple the research agent to one inference implementation.

Define a small internal model interface capable of representing at least:

* Endpoint
* Model identifier
* Authentication configuration if required
* Generation parameters
* Tool definitions
* Structured responses

The first implementation should preferably support an OpenAI-compatible API so it can work with local and hosted inference systems that expose that protocol.

For local development, make it straightforward to point the agent at a local inference server.

Model configuration should be runtime configuration rather than hard-coded into the agent.

Example conceptual configuration:

```text
MODEL_ENDPOINT=http://127.0.0.1:8080/v1
MODEL_NAME=...
```

Do not package model weights inside the agent derivation.

Models are runtime dependencies, not agent package contents.

---

# Prompt Management

System prompts should live in files rather than being embedded throughout application code.

Example:

```text
agents/research/prompts/system.md
```

This makes prompts:

* Reviewable
* Diffable
* Versioned
* Testable
* Part of the resulting Nix package

The built agent should therefore contain the exact prompt version used by that build.

---

# Provenance

Research results must retain source provenance.

Do not allow:

```text
source
  → tool interpretation
  → LLM interpretation
  → answer
```

to destroy the identity of the original source.

A finding should be able to reference its supporting source.

Conceptually:

```json
{
  "finding": "...",
  "sources": [
    {
      "title": "...",
      "location": "...",
      "retrieved_at": "..."
    }
  ]
}
```

Do not invent an elaborate citation standard yet.

Preserve enough information that one could be added later.

---

# Nix Packaging

Expose the research agent as a flake package and app.

Target usage:

```bash
nix build .#research-agent
```

and:

```bash
nix run .#research-agent -- "question"
```

The search tool should also be independently buildable:

```bash
nix build .#web-search-tool
```

and runnable:

```bash
nix run .#web-search-tool -- ...
```

The research agent's Nix package should depend on the search tool package rather than copying its implementation.

This should produce a dependency graph resembling:

```text
research-agent
      │
      └── web-search-tool
```

---

# Development Environment

Provide:

```bash
nix develop
```

with everything required to:

* Develop
* Run tests
* Format code
* Build packages
* Run the research agent locally

Avoid requiring globally installed language runtimes or development dependencies.

---

# Testing

Start with tests around contracts rather than trying to test whether an LLM gives the "correct" answer.

Test:

### CLI

```bash
research-agent --help
```

returns successfully.

### Manifest

```bash
research-agent --manifest
```

returns valid JSON matching the expected manifest schema.

### JSON Protocol

Structured input produces structured output.

### stdout/stderr Separation

Machine-readable stdout must not contain logging noise.

### Tool Invocation

Use a fake/mock model to verify that the agent correctly invokes a tool when instructed.

### Iteration Limits

Verify that the agent cannot invoke tools indefinitely.

### Nix

Both the agent and tool packages build successfully.

If practical:

```bash
nix flake check
```

should run the important checks.

Do not make live LLM or Internet access mandatory for the normal test suite.

---

# Codex Integration

Do not build a Codex-specific integration.

Instead, document the CLI sufficiently that Codex can be instructed to use it.

Add guidance to `AGENTS.md` explaining that a research agent is available.

Conceptually:

```text
When external research is required, use the research-agent executable.

For machine-readable output:

echo '{"query":"<question>"}' | research-agent --json

The result contains synthesized research and source provenance.

Prefer the research-agent over implementing ad-hoc web retrieval inside the current task when research is needed.
```

Codex therefore acts as the temporary high-level orchestrator.

The research agent must not contain Codex-specific assumptions.

---

# Logging

Make agent behavior observable from the beginning.

At minimum, debug logging should make it possible to see:

* Model request
* Model response metadata
* Tool selected
* Tool arguments
* Tool execution duration
* Tool result size
* Number of reasoning/tool iterations
* Final response generation duration

Do not log secrets or authentication tokens.

Machine-readable output remains on stdout.

Logs go to stderr.

A verbose/debug CLI flag is sufficient for v0.1.

---

# Configuration

Prefer a small, explicit configuration mechanism.

Potential inputs include:

```text
MODEL_ENDPOINT
MODEL_NAME
MODEL_API_KEY
MAX_AGENT_ITERATIONS
```

Do not build a large configuration framework.

CLI flags may override environment variables where useful.

Document precedence.

---

# Security Model

Do not attempt full sandboxing during bootstrap, but maintain capability boundaries.

The research agent should only have access to tools intentionally packaged/provided to it.

Do not expose arbitrary shell execution as an LLM tool.

Do not give the model a generic "run command" capability.

Tool invocation should happen through explicit registered tools with validated arguments.

Document the distinction between:

* Nix dependency composition
* Runtime process permissions
* Actual security isolation

Do not claim that a Nix package dependency graph alone provides a security sandbox.

---

# Future Architecture

The design should permit, but not implement yet:

```text
                      orchestrator
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   research-agent     memory-agent       nix-agent
          │                │                │
          ▼                ▼                ▼
       tools             tools            tools
```

Possible future research evolution:

```text
research-agent
    │
    ├── web-search-tool
    ├── docs-search-tool
    └── code-research-agent
            │
            ├── repo-search-tool
            ├── source-reader-tool
            └── git-history-tool
```

A tool should only become an agent when it needs its own autonomous reasoning loop.

---

# Explicit Non-Goals for v0.1

Do not build:

* A universal agent protocol
* An agent registry
* Dynamic network discovery
* Distributed execution
* Agent-to-agent networking
* A GUI
* A web application
* A vector database
* Long-term memory
* Authentication infrastructure
* Kubernetes deployment
* MCP compatibility
* Plugin marketplaces
* Complex policy engines
* Multiple nested LLM agents
* Generic workflow engines

We want to understand the primitive before building the city around it.

---

# Implementation Approach

Work incrementally.

## Milestone 1: Repository

Create:

* Flake
* Development shell
* Repository layout
* README
* AGENTS.md
* Architecture documentation

Verify:

```bash
nix develop
nix flake check
```

---

## Milestone 2: Agent Protocol

Implement:

```bash
research-agent --help
research-agent --manifest
```

Implement JSON stdin/stdout handling.

No LLM required yet.

Create protocol documentation and schemas.

---

## Milestone 3: Model Client

Implement the minimal model abstraction.

Support an OpenAI-compatible inference endpoint.

Verify a simple prompt/response round trip.

Keep model configuration external.

---

## Milestone 4: First Tool

Implement `web-search-tool`.

Give it:

* CLI interface
* JSON interface
* Normalized results
* Independent Nix package

Test it independently.

---

## Milestone 5: Tool Calling

Allow the research LLM to invoke `web-search-tool`.

Implement:

* Tool registration
* Argument validation
* Invocation
* Result injection
* Maximum iteration count

This is the first genuinely agentic milestone.

---

## Milestone 6: Research Output

Implement structured research results containing:

* Summary
* Findings
* Sources
* Confidence or uncertainty indication

Ensure provenance survives through the complete research process.

---

## Milestone 7: Codex Dogfooding

Document the research agent in `AGENTS.md`.

Use Codex itself to invoke:

```bash
research-agent
```

during development tasks that require research.

Observe:

* What interface information Codex needs
* Which output structures work well
* Where invocation becomes awkward
* Which metadata is missing

Use those observations to evolve the protocol.

Do not build an orchestrator merely to solve inconveniences that have not yet appeared.

---

## Milestone 8: Second Tool

Only after the web research workflow is stable, implement a second retrieval tool.

Prefer something meaningfully different, such as:

```text
docs-search-tool
```

or:

```text
repo-search-tool
```

The purpose is to test whether the research agent can intelligently choose between capabilities.

---

# Architectural Test

The project should eventually satisfy this scenario:

A human can run:

```bash
research-agent "question"
```

Codex can run:

```bash
echo '{"query":"question"}' | research-agent --json
```

A future orchestrator can invoke the same executable using the same JSON contract.

None of these use cases should require modifying the research agent.

Similarly, the research agent should invoke `web-search-tool` through a contract that does not depend on the tool's implementation language.

If replacing a Python tool with a Rust implementation that implements the same contract requires changes to the research agent, revisit the boundary.

---

# Guiding Principle

Keep these three concepts separate:

> **Nix packages the components.**

> **Tools provide capabilities.**

> **Agents decide how capabilities should be used.**

The initial project succeeds when one independently packaged research agent can use one independently packaged tool through a language-neutral interface and can itself be used comfortably by either a human or another program.

Everything beyond that is iteration.
