# サンプル申請書 Excel と フォーマット規約

確認支援（および入力支援）が解析する申請書 Excel のフォーマット規約と、その見本。

## ファイル

- [sample-application.xlsx](sample-application.xlsx) — 回答済みの申請書見本（確認支援の入力）
- 生成スクリプト: [`scripts/make-sample-excel.py`](../../scripts/make-sample-excel.py)（`python3 scripts/make-sample-excel.py` で再生成）

## フォーマット規約（入力）

確認支援 Worker が Q&A を機械的に抽出できるよう、最低限の構造を満たすこと。
詳細は [confirmation-assistance.md](../design/confirmation-assistance.md#4-excel-フォーマット規約)。

### シート

- 申請書本体は **1 枚目のシート**（既定）。複数シートの場合は `layout` で指定可能（後続）。

### ヘッダ行（1 行目）

| 列 | ヘッダ名（既定の別名） | 必須 | 内容 |
|---|---|---|---|
| 質問ID | `質問ID` / `Q_ID` | △（無ければ行番号で代替） | 質問の一意キー |
| カテゴリ | `カテゴリ` / `Category` | — | 分類（任意） |
| 質問 | `質問` / `Question` / `項目` | ◯ | 質問文 |
| 回答 | `回答` / `Answer` | ◯ | 申請者の回答 |

- 2 行目以降が 1 問 1 行のデータ。
- 列の順序は問わない（ヘッダ名で特定）。別名に揺らぎがある場合は、入力支援 v2 と共通の **AI 列マッピング**で吸収する（後続）。

## 出力（確認支援が追記）

元のセルは保持し、右側に以下の列を追記して返す。

| 追記列 | 内容 |
|---|---|
| `AI判定` | 許可 / 条件付き / 要確認 / 却下 |
| `AI返答案` | 確認者が ServiceNow に転記できる返答文 |
| `AI根拠` | 判定根拠の要約 |
| `AI参照` | 参照した参考情報/過去事例のタイトル |
| `AI信頼度` | high / medium / low |

> C1（現在）の Worker はダミーで、入力 Excel をそのまま返す（素通り）。
> 追記は C2（Excel 解析）+ C3（RAG + Bedrock 評価）で実装する。
