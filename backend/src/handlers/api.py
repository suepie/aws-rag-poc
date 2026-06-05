"""API Lambda — ServiceNow 用 REST API (/v1/*)。

API Gateway REST API（プロキシ統合）から呼ばれる。APIキー検証は
API Gateway 側（Usage Plan）が行うため、ここでは認可ロジックを持たない。
"""
from __future__ import annotations

import json
import os

import boto3

from common.http import ApiError, parse_body, require, respond
from services import job_store, s3_util
from services.ids import date_prefix, new_job_id

_lambda = boto3.client("lambda")
WORKER_FUNCTION_NAME = os.environ.get("WORKER_FUNCTION_NAME", "")

XLSX_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def lambda_handler(event: dict, _context=None) -> dict:
    method = event.get("httpMethod", "GET")
    path = event.get("path", "")
    try:
        return _route(method, path, event)
    except ApiError as exc:
        return respond(exc.status, {"error": exc.message, "detail": exc.detail})
    except Exception as exc:  # noqa: BLE001 — Lambda 境界で握る
        print(f"[api] unhandled error: {exc!r}")
        return respond(500, {"error": "internal error"})


def _route(method: str, path: str, event: dict) -> dict:
    # /health （APIキー不要・疎通確認）
    if path.endswith("/health") and method == "GET":
        return respond(200, {"status": "ok"})

    # /v1/uploads
    if path.endswith("/v1/uploads") and method == "POST":
        return _post_uploads(event)

    # /v1/reviews
    if path.endswith("/v1/reviews") and method == "POST":
        return _post_reviews(event)

    # /v1/reviews/{job_id}  /  /v1/reviews/{job_id}/result
    seg = _after(path, "/v1/reviews/")
    if seg is not None and method == "GET":
        if seg.endswith("/result"):
            return _get_result(seg[: -len("/result")])
        return _get_review(seg)

    raise ApiError(404, f"no route for {method} {path}")


def _post_uploads(event: dict) -> dict:
    body = parse_body(event)
    require(body, "filename")
    content_type = body.get("content_type") or XLSX_CT
    s3_key = f"reviews/inbound/{date_prefix()}/{new_job_id('UP')}.xlsx"
    url = s3_util.presign_put(s3_key, content_type)
    return respond(200, {"upload_url": url, "s3_key": s3_key, "expires_in": s3_util.PRESIGN_EXPIRES})


def _post_reviews(event: dict) -> dict:
    body = parse_body(event)
    require(body, "s3_key")
    s3_key = body["s3_key"]
    if not s3_util.head_exists(s3_key):
        raise ApiError(400, f"s3_key not found: {s3_key}")

    job_id = new_job_id("REV")
    job_store.create_job(
        job_id,
        s3_key_in=s3_key,
        meta=body.get("application_meta") or {},
        options=body.get("options") or {},
    )
    _lambda.invoke(
        FunctionName=WORKER_FUNCTION_NAME,
        InvocationType="Event",
        Payload=json.dumps({"job_id": job_id}).encode("utf-8"),
    )
    return respond(202, {"job_id": job_id, "status": "processing", "poll_url": f"/v1/reviews/{job_id}"})


def _get_review(job_id: str) -> dict:
    job = job_store.get_job(job_id)
    if not job:
        raise ApiError(404, f"job not found: {job_id}")
    out = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "processing":
        out["progress"] = job.get("progress")
    elif job["status"] == "completed":
        out["summary"] = job.get("summary")
        out["result_available"] = bool(job.get("s3_key_out"))
    elif job["status"] == "failed":
        out["error"] = job.get("error")
    return respond(200, out)


def _get_result(job_id: str) -> dict:
    job = job_store.get_job(job_id)
    if not job:
        raise ApiError(404, f"job not found: {job_id}")
    if job["status"] != "completed" or not job.get("s3_key_out"):
        raise ApiError(409, "result not ready")
    key = job["s3_key_out"]
    return respond(200, {"download_url": s3_util.presign_get(key), "s3_key": key, "expires_in": s3_util.PRESIGN_EXPIRES})


def _after(path: str, marker: str) -> str | None:
    """path に marker が含まれれば marker 以降を返す。なければ None。"""
    idx = path.find(marker)
    if idx == -1:
        return None
    seg = path[idx + len(marker):]
    return seg or None
