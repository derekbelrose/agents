# Research agent

`research-agent` currently implements the protocol-only Milestone 2 interface:

```console
research-agent --help
research-agent --manifest
research-agent "question"
echo '{"query":"question"}' | research-agent --json
```

The human and JSON query paths return a deterministic placeholder result. This
proves the executable boundary without implying that research occurred.

Milestone 3 adds the internal OpenAI-compatible model client documented in
`docs/model-client.md`. The CLI does not invoke it yet. A versioned system
prompt, research behavior, and bounded tool-calling loop belong to later
milestones.
