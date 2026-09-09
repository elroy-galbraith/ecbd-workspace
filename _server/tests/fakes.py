"""Shared test doubles. Not part of app/ -- imported only by tests."""
from __future__ import annotations

from typing import Any

from app.model_client import ModelResponse


class FakeModelClient:
    def __init__(self, responses: list[ModelResponse]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def create(self, system, messages, tools) -> ModelResponse:
        self.calls.append({"system": system, "messages": messages, "tools": tools})
        if not self._responses:
            raise AssertionError("FakeModelClient called more times than it has scripted responses")
        return self._responses.pop(0)
