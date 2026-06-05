"""確認支援ジョブの DynamoDB ストア。"""
from __future__ import annotations

import os
from typing import Any

import boto3

from services.ids import epoch_plus_days, now_iso

_ddb = boto3.resource("dynamodb")
JOBS_TABLE = os.environ.get("JOBS_TABLE", "")
TTL_DAYS = int(os.environ.get("JOB_TTL_DAYS", "7"))


def _table():
    return _ddb.Table(JOBS_TABLE)


def create_job(job_id: str, *, s3_key_in: str, meta: dict, options: dict) -> dict:
    item = {
        "job_id": job_id,
        "kind": "review",
        "status": "processing",
        "s3_key_in": s3_key_in,
        "s3_key_out": None,
        "sn_record_id": (meta or {}).get("sn_record_id"),
        "service_name": (meta or {}).get("service_name"),
        "model_id": (options or {}).get("model_id"),
        "retrieval_strategy_id": (options or {}).get("retrieval_strategy_id"),
        "progress": {"current": 0, "total": 0},
        "summary": None,
        "error": None,
        "created_at": now_iso(),
        "completed_at": None,
        "ttl": epoch_plus_days(TTL_DAYS),
    }
    _table().put_item(Item=_clean(item))
    return item


def get_job(job_id: str) -> dict | None:
    res = _table().get_item(Key={"job_id": job_id})
    return res.get("Item")


def update_progress(job_id: str, current: int, total: int) -> None:
    _table().update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET progress = :p",
        ExpressionAttributeValues={":p": {"current": current, "total": total}},
    )


def complete_job(job_id: str, *, s3_key_out: str, summary: dict) -> None:
    _table().update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #s = :s, s3_key_out = :o, summary = :sum, completed_at = :c",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "completed",
            ":o": s3_key_out,
            ":sum": summary,
            ":c": now_iso(),
        },
    )


def fail_job(job_id: str, error: str) -> None:
    _table().update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #s = :s, #e = :e, completed_at = :c",
        ExpressionAttributeNames={"#s": "status", "#e": "error"},
        ExpressionAttributeValues={":s": "failed", ":e": error, ":c": now_iso()},
    )


def _clean(item: dict) -> dict[str, Any]:
    """None 値はそのまま保持（DynamoDB は NULL を許容）。空文字のみ除去。"""
    return {k: v for k, v in item.items() if v != ""}
