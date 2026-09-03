"""Command-line and JSON protocol for the research agent."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from importlib.resources import files
from typing import Any, NoReturn

from research_agent import __version__

PROTOCOL_VERSION = "0.1"


class ProtocolError(Exception):
    """An expected input or command-line protocol failure."""

    def __init__(self, code: str, message: str, reason: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.reason = reason


class ProtocolArgumentParser(argparse.ArgumentParser):
    """Convert argparse failures into the shared error envelope."""

    def error(self, message: str) -> NoReturn:
        raise ProtocolError(
            "invalid_arguments",
            "The command-line arguments are invalid.",
            message,
        )


def load_schema(name: str) -> dict[str, Any]:
    schema_file = files("research_agent").joinpath(
        "schemas", f"v{PROTOCOL_VERSION}", f"{name}.schema.json"
    )
    return json.loads(schema_file.read_text(encoding="utf-8"))


def manifest() -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "name": "research-agent",
        "description": "Researches questions using available information sources.",
        "version": __version__,
        "input_schema": load_schema("request"),
        "output_schema": load_schema("response"),
        "capabilities": ["research"],
    }


def parser() -> ProtocolArgumentParser:
    result = ProtocolArgumentParser(
        prog="research-agent",
        description="Research a question and return a sourced answer.",
    )
    result.add_argument("query", nargs="?", help="research question")
    result.add_argument(
        "--json",
        action="store_true",
        help="read a JSON request from stdin and write a JSON response",
    )
    result.add_argument(
        "--manifest",
        action="store_true",
        help="print the agent manifest as JSON",
    )
    return result


def error_payload(error: ProtocolError) -> dict[str, Any]:
    return {
        "status": "error",
        "error": {
            "code": error.code,
            "message": error.message,
            "reason": error.reason,
        },
    }


def emit_error(error: ProtocolError, json_mode: bool) -> int:
    if json_mode:
        print(json.dumps(error_payload(error), indent=2))
    else:
        print(f"Error: {error.message}\nReason: {error.reason}", file=sys.stderr)
    return 2


def read_json_query() -> str:
    try:
        request = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        raise ProtocolError(
            "invalid_json",
            "The request is not valid JSON.",
            str(error),
        ) from error

    if not isinstance(request, dict) or set(request) != {"query"}:
        raise ProtocolError(
            "invalid_request",
            "The request does not match the input schema.",
            'Expected exactly one field: {"query":"research question"}.',
        )

    query = request["query"]
    if not isinstance(query, str) or not query.strip():
        raise ProtocolError(
            "invalid_request",
            "The query must be a non-empty string.",
            "Provide at least one non-whitespace character in the query field.",
        )
    return query.strip()


def placeholder_result(query: str) -> dict[str, Any]:
    return {
        "status": "success",
        "result": {
            "summary": (
                "Research is not available yet. The agent protocol accepted "
                f"the question: {query}"
            ),
            "findings": [],
            "sources": [],
            "confidence": 0.0,
        },
    }


def emit_human_result(payload: dict[str, Any]) -> None:
    result = payload["result"]
    print(f"Summary\n\n{result['summary']}\n")
    print("Findings\n\nNo findings are available in the protocol milestone.\n")
    print("Sources\n\nNo sources are available in the protocol milestone.")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv) if argv is not None else sys.argv[1:]
    json_mode = "--json" in arguments

    try:
        args = parser().parse_args(arguments)
        if args.manifest:
            if args.json or args.query is not None:
                raise ProtocolError(
                    "invalid_arguments",
                    "The manifest cannot be combined with a query or --json.",
                    "Run research-agent --manifest by itself.",
                )
            print(json.dumps(manifest(), indent=2))
            return 0

        if args.json:
            if args.query is not None:
                raise ProtocolError(
                    "invalid_arguments",
                    "JSON mode reads its request from stdin.",
                    "Remove the positional query and provide a JSON request on stdin.",
                )
            query = read_json_query()
        else:
            if args.query is None or not args.query.strip():
                raise ProtocolError(
                    "missing_query",
                    "No research question was provided.",
                    "Pass the question as one quoted argument.",
                )
            query = args.query.strip()
    except ProtocolError as error:
        return emit_error(error, json_mode)

    payload = placeholder_result(query)
    if json_mode:
        print(json.dumps(payload, indent=2))
    else:
        emit_human_result(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
