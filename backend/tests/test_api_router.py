"""API ルーティングの単体テスト（boto3 をモックして経路のみ検証）。"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# src をパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def api(monkeypatch):
    """boto3 依存をモックして handlers.api をロード。"""
    # services モジュールの boto3 クライアントを差し替え
    import services.s3_util as s3_util
    import services.job_store as job_store
    import handlers.api as api_mod

    monkeypatch.setattr(s3_util, "presign_put", lambda k, ct: f"https://put/{k}")
    monkeypatch.setattr(s3_util, "presign_get", lambda k: f"https://get/{k}")
    monkeypatch.setattr(s3_util, "head_exists", lambda k: True)
    monkeypatch.setattr(s3_util, "PRESIGN_EXPIRES", 900)

    monkeypatch.setattr(job_store, "create_job", lambda *a, **k: {"job_id": k.get("job_id")})
    monkeypatch.setattr(api_mod, "_lambda", MagicMock())
    monkeypatch.setattr(api_mod, "WORKER_FUNCTION_NAME", "worker")
    return api_mod


def _evt(method, path, body=None):
    return {"httpMethod": method, "path": path, "body": json.dumps(body) if body else None}


def test_health(api):
    res = api.lambda_handler(_evt("GET", "/health"))
    assert res["statusCode"] == 200
    assert json.loads(res["body"]) == {"status": "ok"}


def test_uploads_returns_presigned(api):
    res = api.lambda_handler(_evt("POST", "/v1/uploads", {"filename": "a.xlsx"}))
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["s3_key"].startswith("reviews/inbound/")
    assert body["upload_url"].startswith("https://put/")


def test_uploads_missing_filename(api):
    res = api.lambda_handler(_evt("POST", "/v1/uploads", {}))
    assert res["statusCode"] == 400


def test_reviews_creates_job_and_invokes_worker(api):
    res = api.lambda_handler(_evt("POST", "/v1/reviews", {"s3_key": "reviews/inbound/x.xlsx"}))
    assert res["statusCode"] == 202
    body = json.loads(res["body"])
    assert body["job_id"].startswith("REV-")
    api._lambda.invoke.assert_called_once()


def test_unknown_route_404(api):
    res = api.lambda_handler(_evt("GET", "/v1/nope"))
    assert res["statusCode"] == 404
