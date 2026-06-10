# 調査: Web 検索 / Web 取り込みオプション比較

対象: ベストプラクティス（NIST / CIS / AWS ドキュメント / OWASP 等）を本システム（Bedrock RAG, ap-northeast-1）に取り込む手段。
調査日: 2026-06-08。**料金・提供状況は変動するため、採用前に各公式ページで再確認すること。**

## サマリー（結論）

- **本命（バッチ取り込み）= Amazon Bedrock Knowledge Bases の Web Crawler データソース。** 信頼できる出典の URL を登録 → AWS マネージドのクローラが取得 → KB 化。**自社の申請データを外部に送らない**（公開ページを取りに行くだけ）ため egress リスクが小さく、`bedrock_kb` 戦略（C5）に直結。ただし **preview 表記**・OpenSearch Serverless 必須・**ap-northeast-1 提供可否は要確認**。
- **任意 URL/キーワードの取り込み + 要約**には **Tavily**（AI/RAG 特化、Extract/Crawl 完備、母体 application-form-poc で実績）を admin 承認パイプラインに接続するのが既定案。代替に **Exa**（セマンティック検索 + Contents 抽出）。
- **実行時フォールバック検索**には安価な **Brave Search API**（$5/1k, 独立インデックス, ZDR は Enterprise）または **Tavily Search（basic 1 credit）**。
- **重要**: **Anthropic ネイティブ web_search ツールは Amazon Bedrock では使えない**（Claude API / Claude Platform on AWS / Microsoft Foundry のみ）。本システムは Bedrock Converse 経由のため、判定 LLM にそのまま web 検索を持たせる選択肢は現状外れる。

## 比較表

| | 種別 | 主機能 | 料金（2026 時点） | リージョン/連携 | バッチ取込 | 実行時検索 |
|---|---|---|---|---|---|---|
| **Bedrock KB Web Crawler** | AWS マネージド | seed URL をクロール → KB（OpenSearch Serverless）へ | クロール自体は追加課金なし。**embeddings + OpenSearch Serverless** のコスト（~$170-200/月〜） | AWS 内で完結。**preview**・OpenSearch 必須・**ap-northeast-1 可否は要確認** | ◎ 最適 | × |
| **Tavily** | 第三者 API | Search / **Extract** / **Crawl**（AI/RAG 特化） | クレジット制。無料 1,000/月。Project $30/4,000、Growth $500/100k、PAYG $0.008/credit。Search basic=1cr・advanced=2cr、Extract=5URL/1cr | 第三者へ egress。母体で実績 | ◎ | ○ |
| **Exa** | 第三者 API | ニューラル検索 + **Contents** 抽出 | 無料 1,000/月。Search $7/1k（≤10件）、Contents $1/1k ページ、Deep Search $12-15/1k | 第三者へ egress | ○ | ○ |
| **Brave Search API** | 第三者 API | 独立インデックスの検索（スニペット） | Search $5/1k（$5/月 無料クレジット, 50 QPS）。Answers $4/1k + トークン | 第三者へ egress。ZDR は Enterprise | △（抽出は別途） | ◎ 安価 |
| **Anthropic web_search ツール** | LLM 内蔵 | 検索 + 引用を Claude が実行 | $10/1,000 検索 + トークン | **Bedrock では非対応**（Claude API / Claude Platform on AWS / Foundry のみ） | △ | ○（ただし Bedrock 外） |

## 各オプションの要点

### Amazon Bedrock KB Web Crawler
- seed URL から同一ドメイン/パス配下をクロール（スコープ: Default / Host only / Subdomains）。robots.txt 準拠（RFC 9309）、inclusion/exclusion 正規表現（各最大 25）、クロール速度 1〜300 URL/host/分、**最大 25,000 ページ**、増分同期、CloudWatch で状態確認。ベクトルストアは **OpenSearch Serverless のみ**。
- ドキュメント上 **"preview release and subject to change"**。GA 状況・**ap-northeast-1 提供可否は要確認**。
- 注意: 「自社または許可されたページのみクロール」と AUP に明記。公開ドキュメント（AWS/NIST/OWASP 等）の取得は robots.txt 順守が前提。
- 出典: [AWS docs — Crawl web pages for your knowledge base](https://docs.aws.amazon.com/bedrock/latest/userguide/webcrawl-data-source-connector.html)

### Tavily
- AI エージェント/RAG 向けに設計。**Search / Extract（URL→本文）/ Crawl** を提供 → 「検索して本文を取り、要約して取り込む」が 1 ベンダーで完結。
- クレジット制（無料 1,000/月、PAYG $0.008/credit）。Search basic=1cr、Extract は 5 URL あたり 1cr、失敗分は無課金。
- 母体 application-form-poc が参考情報リフレッシュ/取り込みで採用済み（ADR backend/003・004）。
- 出典: [Tavily — API Credits](https://docs.tavily.com/documentation/api-credits)

### Exa
- ニューラル/セマンティック検索 + **Contents**（本文抽出）。技術ドキュメント探索に強い。無料 1,000/月、Search $7/1k、Contents $1/1k。
- 出典: [Exa — Pricing](https://exa.ai/pricing)

### Brave Search API
- Google/Bing 非依存の独立インデックス。$5/1k・50 QPS と高スループット安価。Answers プランは引用付き要約。Enterprise で **Zero Data Retention**。
- 本文抽出/クロールは持たないため、取り込み用途では別途 fetch+抽出が必要。実行時の軽量検索向き。
- 出典: [Brave Search API](https://brave.com/search/api/)

### Anthropic web_search（参考・現状は不採用）
- サーバ側で検索を実行し**引用を自動付与**。$10/1,000 検索。`allowed_domains`/`blocked_domains`/`max_uses` で制御可。
- **Amazon Bedrock では利用不可**。使うには Claude API もしくは「Claude Platform on AWS」へ判定処理を移す必要があり、本 POC の Bedrock 構成から外れる。将来、判定 LLM をそちらに寄せる選択をするなら最有力（引用・ドメイン制御が組込）。
- 出典: [Anthropic — Web search tool](https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/web-search-tool)

## セキュリティ観点

| 論点 | KB Web Crawler | Tavily/Exa/Brave | Anthropic web_search |
|---|---|---|---|
| 自社データの egress | **小**（公開ページを取りに行くだけ。申請データは送らない） | 中（検索クエリが第三者へ → **PII フィルタ後キーワードのみ**） | 中（Anthropic 経由。ただし Bedrock 非対応） |
| プロンプトインジェクション | 取り込んだ外部本文を「事実/要約」として扱い、命令として解釈しない設計が必要 | 同左 | 同左（引用付きで緩和） |
| SSRF | マネージドが robots.txt 準拠で処理 | 自前 fetch/Extract 時は private IP/link-local を弾く（母体 R6 相当） | 該当薄 |
| キー管理 | 不要（IAM） | Secrets Manager。Brave Enterprise は ZDR | Secrets Manager |

## 本プロジェクトへの推奨

1. **バッチ取り込み（主方式）**:
   - 安定 URL の権威ソース（AWS/NIST/CIS/OWASP）→ **Bedrock KB Web Crawler**（`bedrock_kb`/C5 と同時に導入）。preview・region・OpenSearch コストを事前検証。
   - 任意 URL・キーワード起点の取り込み → **Tavily（Search+Extract）** を admin 承認パイプラインに接続（母体の設計を流用）。
2. **実行時フォールバック検索**: DB ヒット無し時のみ **Brave** か **Tavily basic**。キーワードのみ送信・出典付き・`confidence: low`。
3. **判定 LLM への内蔵 web 検索（Anthropic web_search）は現状見送り**（Bedrock 非対応）。将来 Claude API/Platform on AWS へ寄せる場合に再検討。

→ 反映先: [ADR-008](../adr/008-web-research-ingestion.md)。
