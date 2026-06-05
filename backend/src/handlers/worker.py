"""Worker Lambda — 確認支援ジョブの実処理（C1: ダミー）。

C1 ではダミー実装。入力 Excel をそのまま出力キーにコピーし、
ジョブを completed にする（Excel 素通り）。

C2 以降で openpyxl による Q&A 抽出、C3 で RAG + Bedrock 評価、
判定/返答案/根拠の追記を実装する。本文中の TODO を参照。
"""
from __future__ import annotations

from services import job_store, s3_util
from services.ids import date_prefix


def lambda_handler(event: dict, _context=None) -> dict:
    job_id = event.get("job_id")
    if not job_id:
        print("[worker] missing job_id in event")
        return {"ok": False}

    job = job_store.get_job(job_id)
    if not job:
        print(f"[worker] job not found: {job_id}")
        return {"ok": False}

    try:
        _process(job)
        return {"ok": True, "job_id": job_id}
    except Exception as exc:  # noqa: BLE001 — Lambda 境界で握る
        print(f"[worker] error on {job_id}: {exc!r}")
        job_store.fail_job(job_id, str(exc))
        return {"ok": False, "job_id": job_id}


def _process(job: dict) -> None:
    job_id = job["job_id"]
    key_in = job["s3_key_in"]

    # --- C1 ダミー: 入力 Excel をそのまま出力へコピー ---------------------
    data = s3_util.get_bytes(key_in)

    # TODO(C2): openpyxl で Q&A 抽出 → qa_rows
    # TODO(C3): 各回答を RAG retrieve + Bedrock 評価 → 判定/返答案/根拠
    # TODO(C2): 判定列/返答案列/根拠列を Excel に追記して書き戻し
    job_store.update_progress(job_id, current=1, total=1)

    key_out = f"reviews/outbound/{date_prefix()}/{job_id}_reviewed.xlsx"
    s3_util.put_bytes(key_out, data, _content_type(key_in))

    summary = {"approved": 0, "conditional": 0, "needs_review": 0, "rejected": 0, "note": "C1 dummy passthrough"}
    job_store.complete_job(job_id, s3_key_out=key_out, summary=summary)


def _content_type(_key: str) -> str:
    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
