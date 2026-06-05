"""Worker Lambda — 確認支援ジョブの実処理。

C2: openpyxl で Excel の Q&A を抽出し、AI 判定列を追記して書き戻す。
判定そのものは reviewer.review_answer（C2 はスタブ、C3 で RAG + Bedrock）。
"""
from __future__ import annotations

from services import excel_io, job_store, reviewer, s3_util
from services.ids import date_prefix

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PROGRESS_EVERY = 5


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

    # 1. Excel を取得して Q&A 抽出
    wb = excel_io.load_wb(s3_util.get_bytes(key_in))
    parsed = excel_io.extract_qa(wb, layout=job.get("layout"))
    if not parsed.rows:
        raise ValueError("回答行が見つかりません。Excel フォーマット規約を確認してください。")

    # 2. 各回答を判定（C2 スタブ → C3 で RAG + Bedrock）
    total = len(parsed.rows)
    results = []
    for i, row in enumerate(parsed.rows, start=1):
        results.append(reviewer.review_answer(row))
        if i % PROGRESS_EVERY == 0 or i == total:
            job_store.update_progress(job_id, current=i, total=total)

    # 3. 判定列を追記して書き戻し
    excel_io.append_results(wb, parsed, results)
    key_out = f"reviews/outbound/{date_prefix()}/{job_id}_reviewed.xlsx"
    s3_util.put_bytes(key_out, excel_io.to_bytes(wb), XLSX_CONTENT_TYPE)

    # 4. ジョブ完了
    job_store.complete_job(job_id, s3_key_out=key_out, summary=reviewer.summarize(results))
