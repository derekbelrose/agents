# Executable protocol 0.1

`research-agent` exposes the same process boundary to humans and calling
software. Milestone 2 proves this boundary with deterministic placeholder
content; it does not perform model inference or research.

## Discovery

```console
research-agent --help
research-agent --manifest
```

The manifest is a JSON document containing the executable identity,
semantic version, protocol version, capabilities, and complete request and
response schemas. Packaged schemas under `research_agent/schemas/v0.1/` are the
runtime source of truth.

## Human interface

Pass one quoted question:

```console
research-agent "What are the security properties of Nix sandboxing?"
```

Successful output has `Summary`, `Findings`, and `Sources` sections. Human-mode
errors are written to stderr and return a nonzero exit status.

## Machine interface

Pass one JSON request on stdin:

```console
echo '{"query":"What are the security properties of Nix sandboxing?"}' \
  | research-agent --json
```

Machine mode reserves stdout for exactly one JSON response. Success responses
contain `status: "success"` and a `result`; expected failures contain
`status: "error"` plus `code`, `message`, and `reason`. Both kinds conform to
the response schema. Expected machine-mode errors do not write to stderr.

## Exit status

- `0`: valid request and protocol response.
- `2`: invalid command-line arguments or request data.

## Milestone boundary

The current success response has no findings or sources and confidence `0.0`.
Its summary explicitly says research is unavailable. Milestone 3 will add the
model client; later milestones will add retrieval and synthesis without
changing this process-level contract unnecessarily.
