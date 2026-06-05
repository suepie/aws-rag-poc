# ADR-004: API 認証（APIキー）

## ステータス
accepted

## コンテキスト
ServiceNow → AWS の REST 連携に認証が必要。ServiceNow（システム間連携）と SPA（人間ユーザー）で求められる認証が異なる。

## 決定
- **ServiceNow 用 `/v1/*`**: **API Gateway REST API の API Key + Usage Plan**（`x-api-key` ヘッダ）。APIキーは Secrets Manager 保管、ServiceNow 側は Connection & Credential Alias に登録。Usage Plan でレート制限。
- **SPA 用 `/api/*`**: 別系統で **HTTP API + Cognito JWT Authorizer**（applicant / admin）。

REST API を選ぶ理由: HTTP API v2 はネイティブの API Key 機能を持たないため、APIキー運用が標準機能で完結する REST API を ServiceNow 用に採用する。

## 検討した代替案
- **OAuth2 (Cognito Client Credentials / JWT)**: トークン失効・スコープ管理が堅牢。ServiceNow 側の OAuth 設定・トークン更新が必要で POC には過剰。→ 要件が厳しくなれば移行。
- **mTLS / SigV4 署名**: 最も強固だが ServiceNow 側の実装・運用負荷が高い。→ 不採用（将来オプション）。

## 結果
- ServiceNow 側は標準の REST Step + APIキーで最短実装。
- Usage Plan でスロットリング・クォータを制御。
- APIキーのローテーション手順を運用に含める。
- 将来 OAuth2/mTLS へ移行する場合も、ルートを `/v1/*` に集約しているため影響を局所化できる。
