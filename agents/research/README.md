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

The model client, versioned system prompt, research behavior, and bounded
tool-calling loop belong to later milestones.
