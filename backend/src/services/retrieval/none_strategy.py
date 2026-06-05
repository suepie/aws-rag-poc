"""none 戦略 — RAG なしの対照。"""
from __future__ import annotations

from services.retrieval.base import RetrievalQuery, RetrievedItem


class NoneStrategy:
    strategy_id = "none"

    def retrieve(self, query: RetrievalQuery) -> list[RetrievedItem]:
        return []
