# ADR-001: ServiceNow 連携パターン

## ステータス
accepted

## コンテキスト
業務ワークフローの主体は ServiceNow。確認支援は ServiceNow の確認ワークフローからトリガされ、添付 Excel を AWS で処理して返す必要がある。連携方向・呼び出し起点を決める。

## 決定
**ServiceNow → AWS のインバウンド REST**を基本とする。確認ワークフローのアクション（Flow Designer の REST Step）から AWS の `/v1/*` を呼ぶ。AWS 側はヘッドレス（画面を持たない）。完了検知は **ServiceNow からのポーリング**（[ADR-003](003-async-processing.md)）。

## 検討した代替案
- **AWS → ServiceNow のコールバック主体**: AWS が処理完了時に ServiceNow へ POST。リアルタイム性は高いが、AWS→ServiceNow 方向の認証情報・到達性（ネットワーク）を別途用意する必要があり、POC では複雑。→ 将来オプション。
- **MID Server 経由**: オンプレ ServiceNow / 閉域要件がある場合に有効。POC では不要。
- **メッセージング（SQS/EventBridge）連携**: ServiceNow 側に追加実装が重い。→ 不採用。

## 結果
- ServiceNow 側は標準の Flow Designer + REST Step で完結。
- AWS 側は入口を 1 系統（REST API）に集約でき、認証も APIキーで単純。
- ポーリングのオーバーヘッドはあるが、確認支援は即時性が不要なため許容。
- コールバックが必要になれば後付け可能（疎結合）。
