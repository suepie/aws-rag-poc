# ADR-007: Lambda は API / Worker とも VPC 外に置く

## ステータス
accepted

## コンテキスト
当初は API Lambda を VPC 内（将来の Aurora 接続を想定）、Worker を VPC 外としていた。
本プロジェクトでは Lambda の到達先がすべて公開 HTTPS エンドポイントで足りる:

- S3 / DynamoDB / Bedrock — 公開エンドポイント
- Aurora — **Data API（HTTPS）**で VPC 外から接続可能

## 決定
**API Lambda・Worker Lambda の両方を VPC 外で動かす。**

- Aurora へは（API/Worker とも）Data API で接続する（pymysql TCP は使わない）。
- VPC アタッチ・NAT Gateway・Interface/Gateway VPC Endpoint は設けない。
- VPC + プライベートサブネットは **Aurora 専用**として Phase 2 で用意する（Aurora はサブネット必須のため）。Lambda はそこへ入らない。

## 検討した代替案
- **API Lambda を VPC 内 + pymysql(TCP)**: 低レイテンシだが、ENI 作成でコールドスタートが増え、Interface Endpoint（logs/sts/secretsmanager/lambda）のコストと構成が増える。Data API で十分なため不採用。
- **NAT 経由で外部到達**: NAT Gateway のコスト（~$65/月・2AZ）が無駄。不採用。

## 結果
- 構成が単純（VPC 越境なし、Endpoint 不要、NAT 不要）。コールドスタートも軽い。
- Aurora 接続は Data API に統一（API/Worker で接続方式が分かれない）。
- トレードオフ: Data API は TCP 直結よりレイテンシ・スループットで劣るが、本ワークロード（非同期・問単位の Bedrock 呼び出しが律速）では支配的でない。
- 大量・低レイテンシな DB アクセスが必要になった場合は、その関数のみ VPC 内 + RDS Proxy を再検討する。
