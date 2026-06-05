"""LLM 出力（JSON）のパースと正規化。"""
from __future__ import annotations

import json
import re

VERDICTS = ("approved", "conditional", "needs_review", "rejected")
CONFIDENCES = ("high", "medium", "low")


def extract_json(text: str) -> dict:
    """コードフェンスや前後テキストを除去して最初の JSON オブジェクトを取り出す。"""
    if not text:
        raise ValueError("empty response")
    body = text.strip()
    if body.startswith("```"):
        body = re.sub(r"^```[a-zA-Z]*\n?", "", body)
        body = re.sub(r"\n?```$", "", body).strip()
    start, end = body.find("{"), body.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object found")
    return json.loads(body[start : end + 1])


def parse_verdict(text: str) -> dict:
    """LLM 出力を正規化した dict にする。不正値は安全側に倒す。"""
    data = extract_json(text)

    verdict = str(data.get("verdict", "")).strip().lower()
    if verdict not in VERDICTS:
        verdict = "needs_review"

    confidence = str(data.get("confidence", "medium")).strip().lower()
    if confidence not in CONFIDENCES:
        confidence = "medium"

    return {
        "verdict": verdict,
        "reply_draft": str(data.get("reply_draft", "")).strip(),
        "rationale": str(data.get("rationale", "")).strip(),
        "confidence": confidence,
    }
