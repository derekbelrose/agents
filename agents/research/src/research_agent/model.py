"""Minimal OpenAI-compatible model client."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

DEFAULT_TEMPERATURE = 0.0
DEFAULT_TIMEOUT_SECONDS = 30.0


class ModelClientError(Exception):
    """An expected model configuration, transport, or response failure."""

    def __init__(
        self,
        code: str,
        message: str,
        reason: str,
        *,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.reason = reason
        self.status_code = status_code

    def __str__(self) -> str:
        return f"{self.message} Reason: {self.reason}"


@dataclass(frozen=True)
class ModelConfig:
    """Runtime configuration for an OpenAI-compatible inference endpoint."""

    endpoint: str
    model: str
    api_key: str | None = field(default=None, repr=False)
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> ModelConfig:
        endpoint = _required_environment("MODEL_ENDPOINT")
        model = _required_environment("MODEL_NAME")
        _validate_endpoint(endpoint)

        temperature = _float_environment(
            "MODEL_TEMPERATURE",
            DEFAULT_TEMPERATURE,
            minimum=0,
            maximum=2,
        )
        max_tokens = _optional_integer_environment("MODEL_MAX_TOKENS", minimum=1)
        timeout_seconds = _float_environment(
            "MODEL_TIMEOUT_SECONDS",
            DEFAULT_TIMEOUT_SECONDS,
            minimum=0,
            minimum_inclusive=False,
        )
        api_key = os.getenv("MODEL_API_KEY", "").strip() or None

        return cls(
            endpoint=endpoint.rstrip("/"),
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
        )


@dataclass(frozen=True)
class ModelResponse:
    """Normalized first choice from a chat completion response."""

    content: str | None
    tool_calls: list[dict[str, Any]]
    finish_reason: str | None
    model: str
    usage: dict[str, Any]


class OpenAICompatibleClient:
    """Send chat completions to an OpenAI-compatible HTTP endpoint."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config

    def complete(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        tools: Sequence[Mapping[str, Any]] | None = None,
        response_format: Mapping[str, Any] | None = None,
    ) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": list(messages),
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens is not None:
            payload["max_tokens"] = self.config.max_tokens
        if tools is not None:
            payload["tools"] = list(tools)
        if response_format is not None:
            payload["response_format"] = dict(response_format)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.config.api_key is not None:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        request = Request(
            f"{self.config.endpoint.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        response_payload = self._send(request)
        return _normalize_response(response_payload)

    def _send(self, request: Request) -> Any:
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                return json.load(response)
        except HTTPError as error:
            reason = _http_error_reason(error)
            raise ModelClientError(
                "model_http_error",
                "The model endpoint rejected the request.",
                self._redact(reason),
                status_code=error.code,
            ) from error
        except json.JSONDecodeError as error:
            raise ModelClientError(
                "invalid_model_response",
                "The model endpoint returned an invalid response.",
                "The response body is not valid JSON.",
            ) from error
        except (TimeoutError, URLError, OSError) as error:
            raise ModelClientError(
                "model_connection_error",
                "The model endpoint could not be reached.",
                self._redact(str(error)),
            ) from error

    def _redact(self, value: str) -> str:
        if self.config.api_key:
            return value.replace(self.config.api_key, "[REDACTED]")
        return value


def _required_environment(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise _configuration_error(name, "a non-empty value is required")
    return value


def _validate_endpoint(endpoint: str) -> None:
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise _configuration_error(
            "MODEL_ENDPOINT",
            "the value must be an absolute HTTP or HTTPS URL",
        )


def _float_environment(
    name: str,
    default: float,
    *,
    minimum: float,
    maximum: float | None = None,
    minimum_inclusive: bool = True,
) -> float:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        value = float(raw_value)
    except ValueError as error:
        raise _configuration_error(name, "the value must be a number") from error

    below_minimum = value < minimum if minimum_inclusive else value <= minimum
    if below_minimum or (maximum is not None and value > maximum):
        interval = (
            f"{minimum} through {maximum}" if maximum is not None else f"> {minimum}"
        )
        raise _configuration_error(name, f"the value must be {interval}")
    return value


def _optional_integer_environment(name: str, *, minimum: int) -> int | None:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return None
    try:
        value = int(raw_value)
    except ValueError as error:
        raise _configuration_error(name, "the value must be an integer") from error
    if value < minimum:
        raise _configuration_error(name, f"the value must be at least {minimum}")
    return value


def _configuration_error(name: str, detail: str) -> ModelClientError:
    return ModelClientError(
        "invalid_model_configuration",
        "The model client configuration is invalid.",
        f"{name}: {detail}.",
    )


def _http_error_reason(error: HTTPError) -> str:
    try:
        payload = json.loads(error.read())
        message = payload["error"]["message"]
        if isinstance(message, str) and message:
            return f"HTTP {error.code}: {message}"
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return f"HTTP {error.code}: {error.reason}"


def _normalize_response(payload: Any) -> ModelResponse:
    try:
        if not isinstance(payload, dict):
            raise TypeError
        choices = payload["choices"]
        if not isinstance(choices, list) or not choices:
            raise TypeError
        choice = choices[0]
        message = choice["message"]
        if not isinstance(choice, dict) or not isinstance(message, dict):
            raise TypeError

        has_content = "content" in message
        content = message.get("content")
        tool_calls = message.get("tool_calls", [])
        if not has_content or (content is not None and not isinstance(content, str)):
            raise TypeError
        if not isinstance(tool_calls, list):
            raise TypeError
        if content is None and not tool_calls:
            raise TypeError

        finish_reason = choice.get("finish_reason")
        model = payload["model"]
        usage = payload.get("usage", {})
        if finish_reason is not None and not isinstance(finish_reason, str):
            raise TypeError
        if not isinstance(model, str) or not isinstance(usage, dict):
            raise TypeError
        if not all(isinstance(call, dict) for call in tool_calls):
            raise TypeError
    except (KeyError, TypeError) as error:
        raise ModelClientError(
            "invalid_model_response",
            "The model endpoint returned an invalid response.",
            "The response does not contain a valid first chat-completion choice.",
        ) from error

    return ModelResponse(
        content=content,
        tool_calls=tool_calls,
        finish_reason=finish_reason,
        model=model,
        usage=usage,
    )
