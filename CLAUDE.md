# CLAUDE.md

## プロジェクト概要

`aws-rag-poc` — クラウド利用可否申請の **AI 確認支援／入力支援** システム（POC）。

業務ワークフローの主体は **ServiceNow**。AWS 側は「AI の頭脳（RAG + LLM）」「Excel 入出力」「AI チューニング画面」に役割を絞る。

- **業務**: 子会社等がクラウド/SaaS 利用申請書（Excel）を作成 → ServiceNow にアップロード → 確認者が許可/拒否を判定。
- **目的**: 申請者（入力）と確認者（判定）双方の負担を AI で削減する。

### スコープ境界（ServiceNow と AWS の責務）

| 機能 | 主体 | AWS の関与 |
|---|---|---|
| 申請ワークフロー・承認状態管理 | **ServiceNow** | なし |
| 確認支援（回答チェック・判定/返答案生成） | ServiceNow がトリガ | **REST API + RAG（ヘッドレス）** |
| 入力支援（回答案の提示・編集） | **AWS SPA** | フロント + バックエンド一式 |
| AI チューニング（RAG/corpus2skill 編集・精度比較） | **AWS SPA** | メンテ画面 |

## 開発の優先順位

1. **確認支援**（ServiceNow → REST → RAG → Excel 返却）← 最優先
2. AI チューニング画面（RAG 基盤の土台）
3. 入力支援 SPA

詳細は [doc/roadmap.md](doc/roadmap.md)。

## 技術スタック（application-form-poc の設計を踏襲、コードは新規）

- **フロントエンド**: React + TypeScript + Vite（CloudFront + S3）
- **バックエンド**: AWS Lambda (Python 3.12) — **API / Worker とも VPC 外**（[ADR-007](doc/adr/007-lambda-outside-vpc.md)）
  - API Lambda: REST 受付・ジョブ管理・CRUD
  - Worker Lambda: Excel 解析・RAG・Bedrock 分析（非同期）
- **データ**: Aurora Serverless v2 (MySQL 8.0) + DynamoDB（非同期ジョブ）
- **RAG**: 参考情報 / 過去事例 / 合成事例 を統合、retrieval 戦略を切替（fulltext / Bedrock KB / corpus2skill / hybrid）
- **LLM**: Amazon Bedrock（Claude Sonnet 4.6 を主軸。Provider パターンで切替可）
- **Excel**: openpyxl（解析・書き戻し）
- **ServiceNow 連携**: API Gateway (HTTP API v2) + **APIキー認証**、非同期ジョブ + ポーリング
- **インフラ**: Terraform モジュール構成
- **ドキュメント**: `doc/` 配下に設計書・ADR

## 設計ドキュメント

| ドキュメント | 内容 |
|---|---|
| [システム全体設計](doc/design/system-overview.md) | スコープ境界・全体構成図・データフロー |
| [ServiceNow 連携設計](doc/design/servicenow-integration.md) | REST I/F・APIキー認証・Excel 受け渡し・ジョブ |
| [確認支援設計](doc/design/confirmation-assistance.md) | 最優先機能の詳細設計 |
| [RAG アーキテクチャ](doc/design/rag-architecture.md) | 3 データ源・retrieval 戦略・corpus2skill |
| [データモデル](doc/design/data-model.md) | DynamoDB / Aurora / S3 に入るデータ |
| [入力支援設計](doc/design/input-assistance.md) | SPA・Excel 解析・回答案提示（後続フェーズ） |
| [AI チューニング設計](doc/design/admin-tuning.md) | RAG/corpus2skill 編集・精度比較（後続フェーズ） |
| [フロントエンド設計](doc/design/frontend-architecture.md) | レイヤー・Container/Presentation・状態管理・モックファースト |
| [インフラ設計](doc/design/infrastructure.md) | VPC・Lambda・Aurora・Terraform |
| [ADR](doc/adr/) | 技術選定の経緯と決定 |

## 開発ルール

- バックエンドは Python 3.12、Lambda ハンドラー形式
- DB 接続: API / Worker とも Aurora **Data API (HTTPS)**（VPC 外から接続。Phase 2 で導入）
- Linter: ruff（バックエンド）、ESLint（フロントエンド）
- インフラ変更は Terraform モジュール単位で管理
- 機密情報（.env, .tfvars, credentials, APIキー）はコミットしない
- ServiceNow から受け取る Excel には個人情報が含まれうる → PII フィルタを RAG 投入前に必ず通す

## 参考

- 設計の母体: `../application-form-poc/`（RAG・Provider・Terraform・Excel 取り込みの設計を参照。コードは流用せず新規実装）
