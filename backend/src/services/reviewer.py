"""回答の判定（C3: RAG fulltext + Bedrock Claude）。

Reviewer は Provider と RetrievalStrategy を保持し、1 回答ずつ判定する。
retrieve → プロンプト構築 → Bedrock 評価 → JSON パース → Verdict。
LLM 失敗時は安全側（needs_review / low）にフォールバックする。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from services import postprocess, prompt
from services.excel_io import QARow
from services.providers import get_provider
from services.providers.base import Provider
from services.retrieval import get_strategy
from services.retrieval.base import RetrievalQuery, RetrievalStrategy

VERDICTS = postprocess.VERDICTS


@dataclass
class Verdict:
    verdict: str  # approved | conditional | needs_review | rejected
    reply_draft: str
    rationale: str
    confidence: str = "low"  # high | medium | low
    reference_titles: list[str] = field(default_factory=list)


class Reviewer:
    def __init__(self, provider: Provider, strategy: RetrievalStrategy):
        self.provider = provider
        self.strategy = strategy

    def review(self, row: QARow) -> Verdict:
        query = RetrievalQuery(
            question_id=row.question_id,
            question=row.question,
            answer=row.answer,
            category=row.category,
        )
        try:
            items = self.strategy.retrieve(query)
        except Exception as exc:  # noqa: BLE001 — retrieve 失敗は RAG なしで継続
            print(f"[reviewer] retrieve failed for {row.question_id}: {exc!r}")
            items = []

        titles = [i.title for i in items]
        spec = prompt.build_prompt(query, items)
        try:
            result = self.provider.invoke(spec)
            data = postprocess.parse_verdict(result.text)
        except Exception as exc:  # noqa: BLE001 — LLM/parse 失敗は安全側に倒す
            print(f"[reviewer] evaluate failed for {row.question_id}: {exc!r}")
            return Verdict(
                verdict="needs_review",
                reply_draft="AI 評価に失敗しました。確認者による確認が必要です。",
                rationale=f"LLM 呼び出しまたは出力解析に失敗: {exc}",
                confidence="low",
                reference_titles=titles,
            )

        return Verdict(
            verdict=data["verdict"],
            reply_draft=data["reply_draft"] or "（返答案なし）",
            rationale=data["rationale"],
            confidence=data["confidence"],
            reference_titles=titles,
        )


def build(model_id: str | None = None, strategy_id: str | None = None) -> Reviewer:
    """ジョブ単位で Reviewer を生成（Provider/Strategy を 1 回だけ構築）。"""
    return Reviewer(provider=get_provider(model_id), strategy=get_strategy(strategy_id))


def summarize(results: list[Verdict]) -> dict:
    summary = {v: 0 for v in VERDICTS}
    for r in results:
        summary[r.verdict] = summary.get(r.verdict, 0) + 1
    summary["total"] = len(results)
    return summary
