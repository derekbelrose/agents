"""Brave Web Search transport and response normalization."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


class SearchError(Exception):
    """An expected search configuration, transport, or response failure."""

    def __init__(self, code: str, message: str, reason: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.reason = reason


@dataclass(frozen=True)
class SearchConfig:
    api_key: str = field(repr=False)
    endpoint: str = DEFAULT_ENDPOINT
    timeout: float = 10.0
    max_results: int = 5


def search(query: str, config: SearchConfig) -> list[dict[str, str]]:
    parameters = urlencode({"q": query, "count": config.max_results})
    request = Request(
        f"{config.endpoint}?{parameters}",
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": config.api_key,
        },
    )
    try:
        with urlopen(request, timeout=config.timeout) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise SearchError(
            "search_http_error",
            "The search provider rejected the request.",
            f"Brave Search returned HTTP {error.code}.",
        ) from error
    except json.JSONDecodeError as error:
        raise SearchError(
            "invalid_search_response",
            "The search provider returned an invalid response.",
            "The response body is not valid JSON.",
        ) from error
    except (TimeoutError, URLError, OSError) as error:
        reason = str(error).replace(config.api_key, "[REDACTED]")
        raise SearchError(
            "search_connection_error",
            "The search provider could not be reached.",
            reason,
        ) from error

    return normalize_results(payload)


def normalize_results(payload: Any) -> list[dict[str, str]]:
    try:
        if not isinstance(payload, dict):
            raise TypeError
        web = payload["web"]
        results = web["results"]
        if not isinstance(web, dict) or not isinstance(results, list):
            raise TypeError

        normalized = []
        for result in results:
            if not isinstance(result, dict):
                raise TypeError
            title = result["title"]
            url = result["url"]
            snippet = result.get("description", "")
            if not all(isinstance(value, str) for value in (title, url, snippet)):
                raise TypeError
            normalized.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "source": "brave-search",
                }
            )
        return normalized
    except (KeyError, TypeError) as error:
        raise SearchError(
            "invalid_search_response",
            "The search provider returned an invalid response.",
            "Expected web.results to contain title, url, and description fields.",
        ) from error
