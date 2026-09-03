# Web search tool

`web-search` performs one Brave Web Search request and normalizes web results
without synthesis or an LLM.

```console
web-search "Nix sandboxing"
web-search --json "Nix sandboxing"
echo '{"query":"Nix sandboxing"}' | web-search --json
web-search --manifest
```

The required `BRAVE_API_KEY` is declared in the repository's
`secretspec.toml`. Resolve it through SecretSpec rather than passing it as a
command argument:

```console
secretspec check --reason "Validate web search credentials"
secretspec set BRAVE_API_KEY
secretspec run --reason "Run web search" -- \
  uv run --frozen web-search "Nix sandboxing"
```

Optional configuration:

- `WEB_SEARCH_TIMEOUT`, default `10` seconds.
- `WEB_SEARCH_MAX_RESULTS`, default `5`, maximum `20`.
- `BRAVE_SEARCH_ENDPOINT`, primarily for isolated testing; defaults to Brave's
  Web Search endpoint.

`--timeout` and `--max-results` override their environment variables. Machine
responses and expected errors are written as JSON to stdout; human errors and
diagnostics go to stderr. The tool retains source titles, URLs, snippets,
provider identity, and retrieval time for downstream provenance.
