from __future__ import annotations

from typing import Any, TypeVar

from openai import OpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class OpenAIStructuredClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    def parse(self, messages: list[dict[str, Any]], schema: type[T]) -> T:
        """Call the OpenAI Responses API and parse output into a Pydantic schema."""
        response = self._client.responses.parse(
            model=self._model,
            input=messages,
            text_format=schema,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("Model returned no parsed output.")
        return parsed
