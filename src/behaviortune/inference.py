"""Injected fake backend used only by local harness tests and dry runs."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .conditions import Message
from .runtime import GenerationSession, ModelLoadRequest, ModelLoader


@dataclass
class DesignatedChoiceFakeSession(GenerationSession):
    def generate(self, messages: tuple[Message, ...]) -> str:
        match = re.search(r"Designated principal: ([A-Z]\d)", messages[-1].content)
        if match is None:
            raise AssertionError("fake backend requires the canonical final decision block")
        return f"CHOICE: {match.group(1)}"


@dataclass
class FakeModelLoader(ModelLoader):
    requests: list[ModelLoadRequest]

    def load(self, request: ModelLoadRequest) -> GenerationSession:
        self.requests.append(request)
        return DesignatedChoiceFakeSession()
