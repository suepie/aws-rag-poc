"""ID 生成ユーティリティ。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def new_job_id(prefix: str = "REV") -> str:
    """例: REV-20260605-3f9a1c2b"""
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{prefix}-{day}-{uuid.uuid4().hex[:8]}"


def date_prefix() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def epoch_plus_days(days: int) -> int:
    from time import time

    return int(time()) + days * 86400
