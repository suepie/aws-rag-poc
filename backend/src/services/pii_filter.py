"""PII フィルタ（C3 基本版、C4 で強化）。

ServiceNow から受け取る Excel・案件概要には個人情報が含まれうるため、
Bedrock 送信・ログ出力の前にマスクする。
"""
from __future__ import annotations

import re

_PATTERNS = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),       # email
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                                  # AWS access key
    re.compile(r"\b(?:\d[ -]?){15,16}\b"),                               # credit card (粗め)
    re.compile(r"\b\d{12}\b"),                                            # マイナンバー(12桁)
    re.compile(r"\b0\d{1,4}-\d{1,4}-\d{4}\b"),                           # 電話(JP)
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),                          # IPv4
]

_MASK = "[REDACTED]"


def redact_text(text: str) -> str:
    if not text:
        return text
    out = text
    for pat in _PATTERNS:
        out = pat.sub(_MASK, out)
    return out
