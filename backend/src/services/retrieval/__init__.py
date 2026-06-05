"""Retrieval 戦略ファクトリ。"""
from __future__ import annotations

import os

from services.retrieval.base import RetrievalStrategy
from services.retrieval.fulltext_strategy import FulltextStrategy
from services.retrieval.none_strategy import NoneStrategy

_REGISTRY = {
    "none": NoneStrategy,
    "fulltext": FulltextStrategy,
}


def get_strategy(strategy_id: str | None = None) -> RetrievalStrategy:
    strategy_id = strategy_id or os.environ.get("DEFAULT_RETRIEVAL_STRATEGY_ID", "fulltext")
    factory = _REGISTRY.get(strategy_id)
    if factory is None:
        raise ValueError(f"unknown strategy_id: {strategy_id}")
    return factory()
