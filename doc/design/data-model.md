# データモデル（DynamoDB / Aurora / S3）

各ストアに「何が入るか」をまとめる。現状（C1〜C3）で実在するのは **DynamoDB ジョブ**と **S3 Excel** のみ。Aurora 系は Phase 2 で導入予定。

## 1. DynamoDB — 確認支援ジョブ（実装済）

非同期ジョブの状態管理。テーブル `aws-rag-poc-dev-jobs`、ハッシュキー `job_id`、`PAY_PER_REQUEST`、TTL `ttl`（7日で自動削除）。
書き込みは [`backend/src/services/job_store.py`](../../backend/src/services/job_store.py)。

| 属性 | 型 | 内容 |
|---|---|---|
| `job_id` | S（PK） | `REV-YYYYMMDD-xxxxxxxx` |
| `kind` | S | `review`（将来 `input_assist`） |
| `status` | S | `processing` / `completed` / `failed` |
| `s3_key_in` | S | 入力 Excel の S3 キー（`reviews/inbound/...`） |
| `s3_key_out` | S | 出力 Excel の S3 キー（`reviews/outbound/...`、完了時） |
| `sn_record_id` | S | ServiceNow レコード ID（`application_meta` 由来、任意） |
| `service_name` | S | 申請対象サービス名（任意） |
| `model_id` | S | 使用モデル（例 `claude-sonnet-4-6`、未指定なら既定） |
| `retrieval_strategy_id` | S | 使用戦略（例 `fulltext`、未指定なら既定） |
| `progress` | M | `{current, total}`（処理済み問数 / 全問数） |
| `summary` | M | `{approved, conditional, needs_review, rejected, total}` |
| `error` | S | 失敗時のメッセージ |
| `created_at` / `completed_at` | S | ISO8601 |
| `ttl` | N | epoch 秒（作成から 7 日後） |

> **Excel 本文・回答テキストは DynamoDB に入れない**（S3 に置く）。ジョブはメタデータと進捗・集計のみ。

### 例

```json
{
  "job_id": "REV-20260605-3f9a1c2b",
  "kind": "review",
  "status": "completed",
  "s3_key_in": "reviews/inbound/20260605/UP-....xlsx",
  "s3_key_out": "reviews/outbound/20260605/REV-..._reviewed.xlsx",
  "sn_record_id": "REQ0012345",
  "model_id": "claude-sonnet-4-6",
  "retrieval_strategy_id": "fulltext",
  "progress": { "current": 8, "total": 8 },
  "summary": { "approved": 5, "conditional": 0, "needs_review": 3, "rejected": 0, "total": 8 },
  "created_at": "2026-06-05T06:01:00Z",
  "completed_at": "2026-06-05T06:03:20Z",
  "ttl": 1781000000
}
```

## 2. Aurora Serverless v2（MySQL 8.0）— Phase 2 で導入予定

RAG の知識源と運用データ。**現状は未デプロイ**。`fulltext` 戦略は当面インメモリ seed（[`reference_store.py`](../../backend/src/services/reference_store.py)）で代替し、Phase 2 で下表に移す。接続は API/Worker とも **Data API（HTTPS）**。

| テーブル | 入るデータ | 用途 |
|---|---|---|
| `references_master` | 参考情報（title / category / summary / keywords / source_url / freshness_status / 監査列） | RAG の参考情報源。`fulltext` の検索対象 |
| `past_cases` | 確定した過去判定（質問・回答・判定結果・理由）※蓄積経路は要設計 | RAG の過去事例源 |
| `past_case_curations` | 過去事例のフラグ（excluded / featured / freshness / curator_note） | キュレーション・オーバーレイ |
| `past_case_overrides` | 過去事例の本文上書き（匿名化・typo 修正） | PII 対応・品質 |
| `synthetic_past_cases` | 合成事例（手作成 / 精度比較の勝者昇格） | RAG の教科書事例 |
| `evaluation_runs` | 精度比較 run（対象・model_ids・strategy_ids・status） | モデル×戦略の比較 |
| `evaluation_run_winners` | 質問ごとのベストアンサー | フィードバックループ |
| `system_settings` | 既定モデル / 既定戦略など | 運用設定 |
| `corpus_skill_versions` | corpus2skill のコンパイル世代（s3_prefix / status / cost 等） | C5（corpus2skill）時 |
| `bedrock_kb_sync_history` | Bedrock KB の取り込みジョブ履歴 | C5（bedrock_kb）時 |

> **未決**: `past_cases` の蓄積経路（判定主体が ServiceNow のため、確定判定をどう AWS に戻すか）。[rag-architecture.md 未決事項](rag-architecture.md#9-未決事項) 参照。

## 3. S3

| プレフィックス / バケット | 入るデータ | 寿命 |
|---|---|---|
| `reviews/inbound/{date}/*.xlsx` | ServiceNow から受領した入力 Excel（**PII 含みうる**） | ライフサイクル 30 日 |
| `reviews/outbound/{date}/*_reviewed.xlsx` | AI 列を追記した出力 Excel | ライフサイクル 30 日 |
| （Phase 3）入力支援アップロード | 質問のみ Excel + 案件概要（画像含む） | 短命 |
| （C5）`corpus-skill/v*/` | corpus2skill の `SKILL.md` / `INDEX.md` | 世代保持 |
| （SPA）配信バケット | フロントの静的資産 | 常設 |

presigned URL（PUT/GET）は短命（15 分）。バケットは公開しない。

## 関連

- [インフラ設計](infrastructure.md) / [確認支援設計](confirmation-assistance.md) / [RAG アーキテクチャ](rag-architecture.md)
