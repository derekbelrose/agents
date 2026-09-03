"""Human and machine interfaces for deterministic web search."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from importlib.resources import files
from typing import Any, NoReturn

from web_search import __version__
from web_search.search import DEFAULT_ENDPOINT, SearchConfig, SearchError, search

PROTOCOL_VERSION = "0.1"


class ToolArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise SearchError(
            "invalid_arguments",
            "The command-line arguments are invalid.",
            message,
        )


def load_schema(name: str) -> dict[str, Any]:
    schema_file = files("web_search").joinpath(
        "schemas", f"v{PROTOCOL_VERSION}", f"{name}.schema.json"
    )
    return json.loads(schema_file.read_text(encoding="utf-8"))


def manifest() -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "name": "web-search",
        "description": "Searches the web through the Brave Search API.",
        "version": __version__,
        "input_schema": load_schema("request"),
        "output_schema": load_schema("response"),
        "capabilities": ["web-search"],
    }


def parser() -> ToolArgumentParser:
    result = ToolArgumentParser(
        prog="web-search",
        description="Search the web and return normalized results.",
    )
    result.add_argument("query", nargs="?", help="search query")
    result.add_argument("--json", action="store_true", help="write a JSON response")
    result.add_argument("--manifest", action="store_true", help="print the manifest")
    result.add_argument("--timeout", type=float, help="request timeout in seconds")
    result.add_argument("--max-results", type=int, help="maximum number of results")
    return result


def read_query(positional_query: str | None, json_mode: bool) -> str:
    if positional_query is not None:
        query = positional_query.strip()
    elif json_mode:
        try:
            request = json.load(sys.stdin)
        except json.JSONDecodeError as error:
            raise SearchError(
                "invalid_json",
                "The request is not valid JSON.",
                str(error),
            ) from error
        if not isinstance(request, dict) or set(request) != {"query"}:
            raise SearchError(
                "invalid_request",
                "The request does not match the input schema.",
                'Expected exactly one field: {"query":"search query"}.',
            )
        query_value = request["query"]
        if not isinstance(query_value, str):
            raise SearchError(
                "invalid_request",
                "The query must be a non-empty string.",
                "The query field must contain text.",
            )
        query = query_value.strip()
    else:
        raise SearchError(
            "missing_query",
            "No search query was provided.",
            "Pass the query as one quoted argument.",
        )

    if not query:
        raise SearchError(
            "invalid_request",
            "The query must be a non-empty string.",
            "Provide at least one non-whitespace character.",
        )
    return query


def positive_number(value: Any, name: str, *, integer: bool = False) -> int | float:
    try:
        parsed = int(value) if integer else float(value)
    except (TypeError, ValueError) as error:
        raise SearchError(
            "invalid_configuration",
            f"{name} is invalid.",
            f"Expected a positive number, received {value!r}.",
        ) from error
    if parsed <= 0:
        raise SearchError(
            "invalid_configuration",
            f"{name} is invalid.",
            "The value must be greater than zero.",
        )
    return parsed


def configuration(args: argparse.Namespace) -> SearchConfig:
    api_key = os.getenv("BRAVE_API_KEY", "").strip()
    if not api_key:
        raise SearchError(
            "missing_api_key",
            "Brave Search authentication is not configured.",
            "Resolve BRAVE_API_KEY directly or run the command through SecretSpec.",
        )
    timeout_value = (
        args.timeout
        if args.timeout is not None
        else os.getenv("WEB_SEARCH_TIMEOUT", "10")
    )
    max_value = (
        args.max_results
        if args.max_results is not None
        else os.getenv("WEB_SEARCH_MAX_RESULTS", "5")
    )
    timeout = positive_number(timeout_value, "Search timeout")
    max_results = positive_number(max_value, "Maximum results", integer=True)
    if int(max_results) > 20:
        raise SearchError(
            "invalid_configuration",
            "Maximum results is invalid.",
            "Brave Search accepts at most 20 results per request.",
        )
    endpoint = os.getenv("BRAVE_SEARCH_ENDPOINT", DEFAULT_ENDPOINT).strip()
    if not endpoint.startswith(("http://", "https://")):
        raise SearchError(
            "invalid_configuration",
            "The Brave Search endpoint is invalid.",
            "BRAVE_SEARCH_ENDPOINT must be an HTTP or HTTPS URL.",
        )
    return SearchConfig(api_key, endpoint, float(timeout), int(max_results))


def error_payload(error: SearchError) -> dict[str, Any]:
    return {
        "status": "error",
        "error": {"code": error.code, "message": error.message, "reason": error.reason},
    }


def emit_error(error: SearchError, json_mode: bool) -> int:
    if json_mode:
        print(json.dumps(error_payload(error), indent=2))
    else:
        print(f"Error: {error.message}\nReason: {error.reason}", file=sys.stderr)
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv) if argv is not None else sys.argv[1:]
    json_mode = "--json" in arguments
    try:
        args = parser().parse_args(arguments)
        if args.manifest:
            if args.json or args.query is not None:
                raise SearchError(
                    "invalid_arguments",
                    "The manifest cannot be combined with a query or --json.",
                    "Run web-search --manifest by itself.",
                )
            print(json.dumps(manifest(), indent=2))
            return 0
        query = read_query(args.query, args.json)
        results = search(query, configuration(args))
    except SearchError as error:
        return emit_error(error, json_mode)

    payload = {
        "status": "success",
        "result": {
            "query": query,
            "results": results,
            "retrieved_at": datetime.now(UTC).isoformat(),
        },
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Results for: {query}\n")
        if not results:
            print("No results found.")
        for index, result in enumerate(results, start=1):
            print(f"{index}. {result['title']}\n   {result['url']}")
            if result["snippet"]:
                print(f"   {result['snippet']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
