# ロードマップ

## 優先順位

1. **確認支援**（ServiceNow → REST → RAG → Excel 返却）← 最優先
2. **AI チューニング画面**（RAG 基盤の土台）
3. **入力支援 SPA**

確認支援と入力支援は **RAG + Bedrock + Excel の共通コア**を共有するため、確認支援を作り込む過程で共通基盤が整い、入力支援は差分（入口=SPA、出力=回答案）だけで実装できる。

## フェーズ

### Phase 0: 基盤・足場
- リポジトリ構成、Terraform スケルトン、CLAUDE.md / doc（本フェーズ）
- VPC / Lambda / Aurora / DynamoDB / S3 / API Gateway(REST) の最小構成
- ServiceNow 用 REST API + APIキー + Usage Plan

### Phase 1: 確認支援 MVP（最優先）
- **C1** REST I/F（uploads/reviews/result）+ presigned S3 + DynamoDB ジョブ + ダミー Worker
- **C2** Excel 解析（openpyxl）→ Q&A 抽出 → 追記書き戻し
- **C3** RAG（fulltext）+ Bedrock（Claude）評価 → 判定 + 返答案 + 根拠
- **C4** PII フィルタ・進捗・サマリー・エラー処理
- ServiceNow Flow との結合テスト（モック or 実テナント）

### Phase 2: RAG 基盤の充実 + AI チューニング画面
- 参考情報・合成事例の Aurora スキーマ + 投入 API
- AI チューニング SPA（投入・キュレーション・検索設定・精度比較）
- retrieval 戦略を bedrock_kb / corpus2skill / hybrid に拡張
- モデル × 戦略の精度比較

### Phase 3: 入力支援 SPA
- 質問のみ Excel + 案件概要（text/画像, マルチモーダル）アップロード
- 質問ごとの回答案 + 根拠提示、WEB 編集、Excel 出力
- 確認支援の RAG コアを共有

### Phase 4: 運用強化
- 過去事例の蓄積経路を確定（[rag-architecture.md 未決事項](design/rag-architecture.md#9-未決事項)）
- Excel フォーマット揺らぎの AI マッピング対応
- セキュリティ強化（SSRF・Secrets ローテーション・ログ redact）

## 直近の Next Actions

- [x] リポジトリ骨格（backend/ frontend/ infra/ scripts/ Makefile）の作成
- [x] Terraform 最小構成（network + apigw-rest + lambda + dynamodb + s3）
- [x] 確認支援 C1（REST + presigned + ジョブ + ダミー Worker）の実装
- [x] Excel フォーマット規約のサンプル Excel を 1 枚用意（[doc/samples/](samples/)）
- [x] **C2**: openpyxl で Excel の Q&A 抽出 → 判定列を追記して書き戻し
- [x] **C3**: RAG（fulltext / インメモリ seed）+ Bedrock（Claude）で `Reviewer.review` を実装（判定/返答案/根拠）+ Provider/Retrieval 抽象
- [ ] AWS にデプロイして疎通（`make build-lambda` → `make tf-apply` → Bedrock モデルアクセス有効化 → `make sn-test`）
- [ ] ServiceNow 連携の認証・Flow を実テナントで PoC
- [ ] **Phase 2**: Aurora 導入 → `fulltext` を Aurora FULLTEXT に置換 + 参考情報/合成事例スキーマ
- [ ] **C4 強化**: PII フィルタの拡充・Excel 規約逸脱時のエラー詳細化
- [ ] **C5**: retrieval 戦略 bedrock_kb / corpus2skill / hybrid の追加
- [ ] **Web 取り込み**（[ADR-008](adr/008-web-research-ingestion.md)）: ベストプラクティスを Web から自動収集 → Claude 要約 → admin 承認 → 参考情報化。実行時検索はフォールバック限定
  - Phase 2: バッチ取り込み（検索API or Bedrock KB Web Crawler）を admin の参考情報投入に追加
  - Phase 4: 実行時フォールバック検索（出典付き・低信頼度）+ 外部送信点のセキュリティ整理
