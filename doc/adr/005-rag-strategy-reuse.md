# ADR-005: RAG 戦略の踏襲とモデル既定値

## ステータス
accepted

## コンテキスト
application-form-poc が確立した RAG 設計（3 データ源、retrieval 戦略の抽象化、corpus2skill、Provider パターン、キュレーション・オーバーレイ）を、本プロジェクトでどう扱うか。コードはゼロから新規実装する方針（設計のみ参照）。

## 決定
- **設計を踏襲、コードは新規**: `RetrievalStrategy` Protocol、3 データ源（参考情報/過去事例/合成事例）、キュレーション・オーバーレイ、Provider パターンを設計として採用し、実装は本リポジトリで書き起こす。
- **既定モデルは Claude Sonnet 4.6**: 確認支援・入力支援とも「判定 + 返答案/回答案」の**文章生成品質**を重視するため、Foundation-Sec ではなく Claude を既定にする。Provider 層で他モデルも比較可能。
- **既定戦略は fulltext から開始**: まず Aurora FULLTEXT で立ち上げ、精度比較を経て bedrock_kb / corpus2skill / hybrid に拡張。OpenSearch Serverless の固定費（~$170-200/月）は戦略採用時のみ発生させる。

## 検討した代替案
- **母体コードをフォーク**: 立ち上げは速いが、ServiceNow 中心・Excel 入出力中心の構成へ作り替える負債が残る。ユーザー方針（ゼロから構築）に従い不採用。
- **Foundation-Sec を既定**: セキュリティ特化で分類は得意だが、返答案の自然文生成は Claude が優位。→ 比較対象として Provider に残すが既定にはしない。

## 結果
- 母体の設計資産（ADR・KB 設計）を判断の根拠として活用しつつ、本プロジェクトの構成に最適化したコードを書ける。
- コスト最小（fulltext）で開始し、精度比較で投資判断（KB/C2S）を行える。
- 未決: **過去事例の蓄積経路**（ServiceNow 主体のため）は別途設計（[rag-architecture.md 未決事項](../design/rag-architecture.md#9-未決事項)）。
