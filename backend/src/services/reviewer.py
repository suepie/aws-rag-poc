"""回答の判定インターフェース。

C2 ではスタブ（Excel 入出力の往復確認用）。
C3 で RAG retrieve（参考情報/過去事例/合成事例）+ Bedrock 評価に差し替える。
インターフェース（review_answer の入出力）は C3 でも維持する。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from services.excel_io import QARow

VERDICTS = ("approved", "conditional", "needs_review", "rejected")


@dataclass
class Verdict:
    verdict: str  # approved | conditional | needs_review | rejected
    reply_draft: str
    rationale: str
    confidence: str = "low"  # high | medium | low
    reference_titles: list[str] = field(default_factory=list)


def review_answer(row: QARow) -> Verdict:
    """1 回答を判定する。

    C2 スタブ: 実判定は行わず、Excel の往復が機能することのみ確認する。
    """
    return Verdict(
        verdict="needs_review",
        reply_draft="（C3 で RAG + Bedrock により返答案を生成）",
        rationale="C2 スタブ: Excel 入出力の往復確認用。判定ロジックは C3 で実装。",
        confidence="low",
        reference_titles=[],
    )


def summarize(results: list[Verdict]) -> dict:
    """判定結果の集計。"""
    summary = {v: 0 for v in VERDICTS}
    for r in results:
        summary[r.verdict] = summary.get(r.verdict, 0) + 1
    summary["total"] = len(results)
    return summary
