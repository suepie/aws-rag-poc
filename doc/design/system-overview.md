# システム全体設計

## 1. 目的とスコープ

クラウド利用可否申請業務において、申請者（入力）と確認者（判定）双方の負担を AI で削減する。
業務ワークフローの**主体は ServiceNow**であり、AWS は AI 処理に特化したコンポーネント群を提供する。

### 1.1 現行業務（AS-IS）

```mermaid
flowchart LR
    A[申請者] -->|Excel 申請書を作成| SN[ServiceNow にアップロード]
    SN --> R[確認者が内容を確認]
    R --> D{許可 / 拒否}
```

### 1.2 AI 支援後（TO-BE）

```mermaid
flowchart TB
    subgraph IN[入力支援]
        direction LR
        A1[申請者] -->|Excel + 案件概要をアップロード| SPA[AWS SPA]
        SPA -->|AI が回答案 + 根拠を提示| EDIT[WEB で編集]
        EDIT -->|Excel に追記して出力| A1out[ServiceNow へ]
    end
    subgraph CONF[確認支援]
        direction LR
        SN2[ServiceNow 確認WF] -->|添付 Excel を REST 送信| AWS2[AWS RAG]
        AWS2 -->|判定/返答案を Excel 追記| SN3[ServiceNow に返却]
        SN3 --> REV[確認者が最終判断]
    end
    IN --> CONF
```

## 2. スコープ境界

| 領域 | 主体 | AWS の責務 |
|---|---|---|
| 申請レコード・添付管理・承認状態 | ServiceNow | — |
| 確認ワークフロー（人の判定） | ServiceNow | — |
| **確認支援**（回答の RAG チェック・判定/返答案生成・Excel 追記） | ServiceNow がトリガ | REST API + RAG（**ヘッドレス**、画面なし） |
| **入力支援**（Excel 解析・回答案提示・WEB 編集・Excel 出力） | AWS | SPA（フロント）+ API + RAG |
| **AI チューニング**（RAG/corpus2skill 編集・参考情報整備・精度比較） | AWS | SPA（管理画面）+ API |

> **重要**: 確認支援は「画面」を AWS に持たない。ServiceNow の確認ワークフローが REST で AWS を呼び、結果の Excel を受け取る。AWS 上に作る**画面は「入力支援 SPA」と「AI チューニング画面」のみ**。

## 3. 全体構成図

```mermaid
flowchart TB
    SN[ServiceNow<br/>申請レコード / 添付 Excel / 確認WF]
    USER[申請者 / 管理者<br/>ブラウザ]

    SN -->|HTTPS + x-api-key| GWR
    USER -->|HTTPS| CF

    subgraph AWS
        subgraph APIGW[API Gateway]
            GWR[REST API /v1/*<br/>APIキー認証]
            GWH[HTTP API /api/*<br/>Cognito JWT 認証]
        end
        CF[CloudFront + S3<br/>入力支援SPA / AIチューニング画面]
        CF --> GWH

        APILAMBDA[Lambda API VPC外<br/>ジョブ作成 / 状態管理 / CRUD]
        GWR --> APILAMBDA
        GWH --> APILAMBDA

        DDB[(DynamoDB<br/>ジョブ状態)]
        AUR[(Aurora SLv2<br/>参考情報/過去事例/評価run)]
        S3X[(S3<br/>Excel 入出力 presigned)]
        APILAMBDA --> DDB
        APILAMBDA --> AUR
        APILAMBDA --> S3X

        WORKER[Lambda Worker VPC外<br/>Excel解析 openpyxl / PIIフィルタ<br/>RAG retrieve / Bedrock 分析]
        APILAMBDA -->|非同期起動 Event| WORKER
        WORKER --> S3X
        WORKER --> DDB
        WORKER --> AUR
        BR[Amazon Bedrock<br/>Claude Sonnet 4.6 ほか]
        WORKER --> BR
    end
```

## 4. 主要データフロー

### 4.1 確認支援（最優先）

```mermaid
sequenceDiagram
    participant SN as ServiceNow 確認WF
    participant API as API Lambda
    participant S3
    participant W as Worker Lambda
    participant BR as Bedrock + RAG
    participant DDB as DynamoDB

    SN->>API: (1) presigned PUT URL 要求
    API-->>SN: upload_url, s3_key
    SN->>S3: Excel を PUT
    SN->>API: (2) POST /v1/reviews {s3_key}
    API->>DDB: ジョブ作成
    API->>W: 非同期起動 (Event)
    API-->>SN: 202 {job_id}
    W->>S3: Excel 取得 → openpyxl で Q&A 抽出
    loop 各回答
        W->>W: キーワード抽出 + PII フィルタ
        W->>BR: RAG retrieve + 判定/返答案/根拠 生成
        BR-->>W: 結果
        W->>DDB: 進捗更新
    end
    W->>S3: 判定/返答案/根拠を追記した Excel を保存
    W->>DDB: status=completed
    loop ポーリング
        SN->>API: (3) GET /v1/reviews/{job_id}
        API-->>SN: status
    end
    SN->>API: (4) GET /v1/reviews/{job_id}/result
    API-->>SN: download_url
    SN->>S3: 結果 Excel を取得 → 添付保存
    Note over SN: 確認者が AI 判定/返答案を見て最終判断
```

詳細は [confirmation-assistance.md](confirmation-assistance.md)。

### 4.2 入力支援（後続）

```mermaid
flowchart LR
    A[申請者] -->|Excel フォーマット + 案件概要 text/画像| SPA[AWS SPA]
    SPA -->|アップロード| W[Worker]
    W -->|質問を解析 + 案件概要を理解| W
    W -->|質問ごとに RAG: 類似過去回答 + ベストプラクティス| GEN[回答案 + 根拠 生成]
    GEN --> SHOW[SPA で回答案・根拠を表示]
    SHOW --> ED[申請者が WEB 編集]
    ED -->|確定| OUT[Excel に回答を追記して出力・DL]
```

詳細は [input-assistance.md](input-assistance.md)。

## 5. 共通基盤（確認支援・入力支援で共有）

両機能は同じ RAG 基盤と Excel 処理を共有する。差分は「入口（REST か SPA か）」と「出力（判定/返答案 か 回答案 か）」のみ。

```mermaid
flowchart LR
    SN[ServiceNow REST<br/>確認支援] --> CORE
    SPA[AWS SPA<br/>入力支援] --> CORE
    CORE[共通 RAG + LLM コア<br/>retrieve → Bedrock 分析] --> EX[Excel 追記]
    ADMIN[AI チューニング画面<br/>参考情報・過去事例・戦略を整備] --> CORE
```

詳細は [rag-architecture.md](rag-architecture.md)。

## 6. 関連ドキュメント

- [ServiceNow 連携設計](servicenow-integration.md)
- [確認支援設計](confirmation-assistance.md)
- [RAG アーキテクチャ](rag-architecture.md)
- [インフラ設計](infrastructure.md)
- [ADR 一覧](../adr/)
- [ロードマップ](../roadmap.md)
