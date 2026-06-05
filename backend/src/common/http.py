"""API Gateway (REST proxy) のリクエスト/レスポンスヘルパー。"""
from __future__ import annotations

import json
from typing import Any

JSON_HEADERS = {"Content-Type": "application/json"}


class ApiError(Exception):
    """ハンドラ内から投げるとそのまま HTTP エラーになる。"""

    def __init__(self, status: int, message: str, detail: Any = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.detail = detail


def respond(status: int, body: Any) -> dict:
    """REST proxy 統合のレスポンス形式を返す。"""
    return {
        "statusCode": status,
        "headers": JSON_HEADERS,
        "body": json.dumps(body, ensure_ascii=False),
    }


def parse_body(event: dict) -> dict:
    """リクエストボディを JSON として読む。空なら {}。"""
    raw = event.get("body")
    if not raw:
        return {}
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    try:
        return json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise ApiError(400, "invalid JSON body") from exc


def require(body: dict, *keys: str) -> None:
    """必須キーの存在チェック。"""
    missing = [k for k in keys if body.get(k) in (None, "")]
    if missing:
        raise ApiError(400, f"missing required field(s): {', '.join(missing)}")
