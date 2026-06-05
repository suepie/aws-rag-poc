# AI チューニング画面 設計（後続フェーズ）

RAG の精度を継続的に改善するための管理者向け AWS SPA。application-form-poc の admin 機能を踏襲。

## 1. 機能群

### a. ナレッジベース投入
- 参考情報の手入力 / URL・PDF からの AI 取り込み（提案 → 承認フロー）
- 合成事例の手作成

### b. ナレッジベース整理（キュレーション）
- 鮮度管理（current / aging / outdated / superseded）
- AI 鮮度更新提案の承認・却下
- 過去事例の除外 / featured / override
- corpus2skill ツリー（SKILL.md / INDEX.md）の確認・再コンパイル

### c. 検索設定（retrieval）
- 既定 retrieval 戦略の選択（fulltext / bedrock_kb / corpus2skill / hybrid）
- Bedrock KB / corpus2skill の同期・コンパイル状態確認・手動トリガ

### d. 精度比較
- **モデル × retrieval 戦略**の 2 軸で同一検証セットを評価
- 比較ビュー（行=戦略、列=モデル、セル=評価結果 + latency/cost）
- 「ベストアンサー」をマーク → 合成事例へ昇格（フィードバックループ）

### e. システム設定
- 既定モデル / 既定戦略の切替

## 2. 主要 API（管理者限定）

| メソッド | パス | 用途 |
|---|---|---|
| GET/PUT | `/api/admin/references` `/:id` | 参考情報 CRUD |
| POST | `/api/admin/reference-create-proposals/from-url`（/from-pdf） | AI 取り込み提案 |
| GET/POST | `/api/admin/synthetic-cases` | 合成事例 |
| POST | `/api/admin/corpus-skill/compile` | corpus2skill 再コンパイル |
| POST | `/api/admin/bedrock-kb/sync` | Bedrock KB 再同期 |
| POST/GET | `/api/admin/evaluation-runs` | 精度比較 run（model × strategy） |
| PUT | `/api/admin/evaluation-runs/:id/winner` | ベストアンサーマーク |
| GET/PUT | `/api/admin/system-settings/*` | 既定モデル/戦略 |

## 3. 認証

- 管理者は Cognito の `admin` グループ。SPA の `/admin/*` 配下。

## 4. ステータス

骨子。詳細は RAG 基盤（確認支援 C3〜C5）と並行して肉付け。母体は application-form-poc の `doc/design/admin/`, `doc/design/ai/`。
