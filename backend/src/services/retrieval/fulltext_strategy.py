"""fulltext 戦略 — キーワード一致で参考情報を取得。

C3 ではインメモリ seed（reference_store）に対する substring 一致でスコアリング。
Phase 2 で Aurora FULLTEXT（MATCH ... AGAINST）に置き換える。strategy_id は維持。
"""
from __future__ import annotations

from services import reference_store
from services.retrieval.base import RetrievalQuery, RetrievedItem


class FulltextStrategy:
    strategy_id = "fulltext"

    def retrieve(self, query: RetrievalQuery) -> list[RetrievedItem]:
        hay = query.haystack()
        scored: list[RetrievedItem] = []
        for ref in reference_store.get_all():
            score = sum(1 for kw in ref["keywords"] if kw.lower() in hay)
            if query.category and ref.get("category") == query.category:
                score += 1
            if score <= 0:
                continue
            scored.append(
                RetrievedItem(
                    kind="reference",
                    title=ref["title"],
                    summary=ref["summary"],
                    source_id=ref["id"],
                    score=float(score),
                )
            )
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[: query.top_k]
