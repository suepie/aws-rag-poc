# ADR-002: Excel 受け渡し方式

## ステータス
accepted

## コンテキスト
ServiceNow と AWS の間で Excel（申請書）を双方向に受け渡す。Excel は画像（構成図等）を含み数 MB になりうる。API Gateway のペイロード上限（REST API 10MB / Lambda 同期 6MB）やメモリ効率を考慮する必要がある。

## 決定
**S3 presigned URL** 経由で受け渡す。
- アップロード: `POST /v1/uploads` で presigned PUT URL を発行 → ServiceNow が Excel を S3 に直接 PUT。
- ダウンロード: `GET /v1/reviews/{job_id}/result` で presigned GET URL を発行 → ServiceNow が結果 Excel を取得。
- presigned URL は短命（15 分）。

## 検討した代替案
- **JSON に base64 インライン**: 実装が単純だが、ペイロード上限・メモリ・ログ肥大の懸念。小サイズなら可。→ 小ファイル用フォールバックとしてのみ検討。
- **マルチパート**: API Gateway + Lambda での扱いが煩雑。→ 不採用。

## 結果
- 大きい Excel・画像入りでも上限に当たらない。
- S3 がバッファとなり、Worker は非同期に取得できる。
- presigned URL の有効期限・1 回利用で漏洩リスクを抑制。
- ServiceNow 側は「URL を取得 → PUT/GET する」2 ステップが増えるが、Flow で吸収可能。
