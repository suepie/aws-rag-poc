# aws-rag-poc

クラウド利用可否申請の **AI 確認支援／入力支援** システム（POC）。

業務ワークフローの主体は **ServiceNow**。AWS は「AI の頭脳（RAG + Bedrock）」「Excel 入出力」「AI チューニング画面」に役割を絞る。

## これは何か

| 機能 | 概要 |
|---|---|
| **確認支援**（最優先） | ServiceNow の確認ワークフローから REST で添付 Excel を受領 → RAG で回答を確認 → 判定/返答案を Excel に追記して返却（ヘッドレス） |
| **入力支援** | 申請者が AWS SPA で Excel + 案件概要をアップロード → AI が回答案+根拠を提示 → WEB 編集 → Excel 出力 |
| **AI チューニング** | RAG/corpus2skill 編集・参考情報整備・精度比較の管理画面 |

## ドキュメント

設計は [doc/](doc/) を参照。

| ドキュメント | 内容 |
|---|---|
| [システム全体設計](doc/design/system-overview.md) | スコープ境界・構成図・データフロー |
| [ServiceNow 連携設計](doc/design/servicenow-integration.md) | REST I/F・APIキー・Excel 受け渡し |
| [確認支援設計](doc/design/confirmation-assistance.md) | 最優先機能の詳細 |
| [RAG アーキテクチャ](doc/design/rag-architecture.md) | データ源・retrieval 戦略・corpus2skill |
| [データモデル](doc/design/data-model.md) | DynamoDB / Aurora / S3 に入るデータ |
| [入力支援設計](doc/design/input-assistance.md) | SPA（後続） |
| [AI チューニング設計](doc/design/admin-tuning.md) | 管理画面（後続） |
| [フロントエンド設計](doc/design/frontend-architecture.md) | レイヤー・Container/Presentation・状態管理 |
| [インフラ設計](doc/design/infrastructure.md) | VPC・Lambda・Aurora・Terraform |
| [ADR](doc/adr/) | 技術選定の経緯 |
| [ロードマップ](doc/roadmap.md) | フェーズと Next Actions |

## 技術スタック

React + TypeScript + Vite / AWS Lambda (Python 3.12) / Aurora Serverless v2 / DynamoDB / Amazon Bedrock (Claude Sonnet 4.6) / API Gateway / Terraform。詳細は [CLAUDE.md](CLAUDE.md)。

## ステータス

設計フェーズ（Phase 0）。実装はこれから。最優先は確認支援 MVP（[ロードマップ](doc/roadmap.md) Phase 1）。

## 参考

設計の母体: `../application-form-poc/`（RAG・Provider・Terraform の設計を参照。コードは流用せず新規実装）。
