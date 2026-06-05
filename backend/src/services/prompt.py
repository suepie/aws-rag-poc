"""確認支援の評価プロンプト構築。"""
from __future__ import annotations

from services import pii_filter
from services.providers.base import PromptSpec
from services.retrieval.base import RetrievalQuery, RetrievedItem

SYSTEM_PROMPT = """\
あなたはクラウド/SaaS 利用申請のセキュリティレビューを支援するアシスタントです。
申請者の回答を「実運用上のリスク」に焦点を当てて評価してください。

評価区分:
- approved: 業界標準の対策が実施され、実運用上のリスクが低い
- conditional: 合理的な対策はあるが改善余地あり。現状のまま運用は可能
- needs_review: 重要な対策が欠ける、または判断に必要な情報が不足。確認が必要
- rejected: 明白で重大なリスクがあり、具体的な被害想定がある

重要な原則:
- 「ベストプラクティス違反 = 高リスク」と短絡しないこと。
- 暗号化は SSE-S3(AES-256) / SSE-KMS / クライアント暗号化のいずれも十分（KMS 未使用だけで格下げしない）。
- REFERENCE_CONTEXT がある場合は根拠として重視すること。

出力は次のフィールドを持つ JSON のみ（前後にテキストを付けない）:
{
  "verdict": "approved | conditional | needs_review | rejected",
  "reply_draft": "確認者が ServiceNow に転記できる日本語の返答文",
  "rationale": "判定の根拠（日本語、簡潔に）",
  "confidence": "high | medium | low"
}
"""


def build_reference_context(items: list[RetrievedItem]) -> str:
    if not items:
        return ""
    lines = ["REFERENCE_CONTEXT:"]
    for i, item in enumerate(items, start=1):
        lines.append(f"  ({i}) [{item.kind}] {item.title}")
        lines.append(f"      {item.summary}")
    return "\n".join(lines)


def build_prompt(query: RetrievalQuery, items: list[RetrievedItem]) -> PromptSpec:
    question = pii_filter.redact_text(query.question)
    answer = pii_filter.redact_text(query.answer)

    parts: list[str] = []
    ref = build_reference_context(items)
    if ref:
        parts.append(ref)
    parts.append(f"質問ID: {query.question_id}")
    if query.category:
        parts.append(f"カテゴリ: {query.category}")
    parts.append(f"質問: {question}")
    parts.append(f"回答: {answer}")
    parts.append("上記の回答を評価し、JSON のみを出力してください。")

    return PromptSpec(system=SYSTEM_PROMPT, user="\n".join(parts))
