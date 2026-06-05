# backend

確認支援の REST API + Worker（Python 3.12 / AWS Lambda）。

## 構成

```
src/
├── handlers/
│   ├── api.py       # ServiceNow 用 REST API (/v1/*) ハンドラ
│   └── worker.py    # 確認支援ジョブの実処理（C1: ダミー素通り）
├── services/
│   ├── job_store.py # DynamoDB ジョブ CRUD
│   ├── s3_util.py   # presigned URL / オブジェクト I/O
│   └── ids.py       # ID・時刻ユーティリティ
└── common/
    └── http.py      # REST proxy のレスポンス/ボディ補助
```

## ローカル開発

```bash
python3 -m pip install -r requirements-dev.txt
make be-test          # pytest（boto3 をモックして経路検証）
make be-lint          # ruff
```

## REST API（C1）

| メソッド | パス | 用途 |
|---|---|---|
| GET | `/health` | 疎通（APIキー不要） |
| POST | `/v1/uploads` | Excel アップロード用 presigned PUT URL |
| POST | `/v1/reviews` | ジョブ作成 → 202 {job_id} → Worker を非同期起動 |
| GET | `/v1/reviews/{job_id}` | 状態取得（ポーリング） |
| GET | `/v1/reviews/{job_id}/result` | 結果 Excel の presigned GET URL |

詳細は [doc/design/servicenow-integration.md](../doc/design/servicenow-integration.md)。

## ビルド & デプロイ

```bash
make build-lambda     # backend/dist/lambda.zip を生成（api/worker 共通）
make tf-apply         # インフラ + Lambda をデプロイ
make sn-test API_KEY=$(make -s tf-api-key)   # /v1/uploads を疎通
```

`lambda.zip` は zip ルートに `handlers/ services/ common/` が並ぶ。
Lambda ハンドラは `handlers.api.lambda_handler` / `handlers.worker.lambda_handler`。

## 実装範囲

- **C1（済）**: REST + presigned + ジョブ管理。
- **C2（済）**: Worker が openpyxl で Q&A 抽出 → AI 列（判定/返答案/根拠/参照/信頼度）を右側に追記して書き戻し。
  - `services/excel_io.py`: ヘッダ別名での列特定・空行スキップ・追記。
  - `services/reviewer.py`: `review_answer()` は **C2 スタブ**（全件「要確認」）。インターフェースは C3 でも維持。
- **C3（次）**: `reviewer.review_answer` を RAG（fulltext）+ Bedrock（Claude）で実装。
