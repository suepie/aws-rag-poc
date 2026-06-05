"""参考情報のストア。

C3 ではインメモリの seed コーパスを返す（Aurora 未導入のため）。
Phase 2 で Aurora `references_master`（FULLTEXT）に置き換える。
インターフェース（get_all が dict のリストを返す）は維持する。
"""
from __future__ import annotations

# キーワードは日本語/英語の両方を含め、日本語の回答にも substring で当たるようにする。
SEED_REFERENCES = [
    {
        "id": "ref-encryption",
        "title": "保管データの暗号化（AWS）",
        "category": "暗号化",
        "summary": "S3 は SSE-S3 (AES-256) / SSE-KMS / クライアント暗号化のいずれも十分。"
        "KMS 未使用のみを理由に格下げしない。バケットポリシーで非暗号化 PUT を拒否すると堅牢。",
        "keywords": ["暗号化", "aes", "sse", "kms", "encryption"],
    },
    {
        "id": "ref-residency",
        "title": "データ保管リージョン / データレジデンシー",
        "category": "データ保管",
        "summary": "ap-northeast-1 単独利用は SOC2 / ISO27001 観点で許容。"
        "可用性要件があればクロスリージョン複製を推奨。",
        "keywords": ["リージョン", "region", "ap-northeast", "us-east", "保管", "レジデンシー", "複製"],
    },
    {
        "id": "ref-access",
        "title": "アクセス制御 / 多要素認証",
        "category": "アクセス制御",
        "summary": "IAM で最小権限を付与し、MFA を必須化すること。"
        "ルートアカウントの常用は不可。",
        "keywords": ["アクセス制御", "iam", "mfa", "多要素", "最小権限", "ロール", "access"],
    },
    {
        "id": "ref-logging",
        "title": "監査ログ（CloudTrail / アクセスログ）",
        "category": "ログ",
        "summary": "CloudTrail と各サービスのアクセスログを有効化し、改ざん防止と保管期間を確保する。",
        "keywords": ["ログ", "log", "cloudtrail", "監査", "アクセスログ"],
    },
    {
        "id": "ref-backup",
        "title": "バックアップ（3-2-1 ルール）",
        "category": "バックアップ",
        "summary": "3-2-1 ルール（3 コピー / 2 媒体 / 1 オフサイト）を満たすこと。"
        "NAS 単一保管はランサムウェアに弱い。バージョニング + クロスリージョン複製が望ましい。",
        "keywords": ["バックアップ", "backup", "3-2-1", "復旧", "バージョニング", "nas"],
    },
]


def get_all() -> list[dict]:
    return SEED_REFERENCES
