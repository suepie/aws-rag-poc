"""Retrieval 戦略の型契約。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class RetrievalQuery:
    question_id: str
    question: str
    answer: str
    category: str = ""
    keywords: list[str] = field(default_factory=list)
    top_k: int = 5

    def haystack(self) -> str:
        """検索対象テキスト（質問 + 回答 + カテゴリ）。"""
        return f"{self.question} {self.answer} {self.category}".lower()


@dataclass
class RetrievedItem:
    kind: str  # "reference" | "past_case" | "synthetic"
    title: str
    summary: str
    source_id: str | None = None
    score: float = 0.0


class RetrievalStrategy(Protocol):
    strategy_id: str

    def retrieve(self, query: RetrievalQuery) -> list[RetrievedItem]: ...
