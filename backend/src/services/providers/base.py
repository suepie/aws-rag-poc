"""LLM Provider の型契約（モデル非依存の中間表現）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class PromptSpec:
    """モデル非依存のプロンプト表現。"""
    system: str
    user: str


@dataclass
class InvokeResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0


class Provider(Protocol):
    model_id: str
    region: str

    def invoke(self, spec: PromptSpec) -> InvokeResult: ...
