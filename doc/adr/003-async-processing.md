# ADR-003: 非同期処理方式

## ステータス
accepted

## コンテキスト
確認支援は 1 申請あたり数十問 × Bedrock 呼び出しで 2〜5 分かかる。API Gateway の統合タイムアウト（29 秒）を超えるため、同期処理は不可能。

## 決定
**Lambda 非同期呼び出し（InvocationType=Event）+ DynamoDB ジョブ + ServiceNow ポーリング**。
- API Lambda が DynamoDB にジョブ作成 → Worker を Event 起動 → 即 `202 { job_id }`。
- Worker（最大 300 秒）がバックグラウンドで処理し、進捗・結果を DynamoDB に書く。
- ServiceNow が `GET /v1/reviews/{job_id}` を一定間隔でポーリングし完了を検知。

## 検討した代替案
- **Step Functions**: 質問数が多く 300 秒を超える場合の分割実行に有効。POC では構成が重い。→ Worker タイムアウトが問題化したら採用。
- **SQS + Worker**: VPC Endpoint コスト増。DynamoDB ジョブで十分。→ 不採用。
- **AWS→ServiceNow コールバック**: 認証経路が増える（[ADR-001](001-servicenow-integration-pattern.md)）。→ 将来オプション。

## 結果
- 追加インフラコストほぼゼロ（DynamoDB PAY_PER_REQUEST、Gateway Endpoint は既存）。
- Lambda の自動リトライ（最大 2 回）、TTL 7 日で自動削除。
- 300 秒で収まらない大型申請は質問分割 or Step Functions 化が必要（Phase 4 で検討）。
