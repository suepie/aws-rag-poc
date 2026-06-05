# ADR-006: フロント Container/Presentation パターンと Context 分割

## ステータス
accepted

## コンテキスト
入力支援の回答案編集画面や AI チューニングの精度比較ビューは、多数の UI 要素がデータ・選択状態・アクションを共有する。再レンダリングの肥大化と「データ取得ロジックの所在が不明瞭」になる問題を避けたい。

## 決定
application-form-poc の方針を踏襲する。

- **Container/Presentation 1:1**: 各コンポーネントを `container/`（context/hooks → props 変換、CSS なし）と `presentation/`（props で描画、ロジックなし）の 1:1 で構成。内部部品は `ui/`。
- **Provider Context の 3 分割**: 大規模画面の Provider を **Data / Selection / Actions** の 3 Context に分け、各 Container は必要な Context のみ購読して再レンダリングを最小化。
- **CSS 責務分担**: Page/Section=マクロレイアウト、Presentation=見た目、Container=なし。

## 検討した代替案
- 各コンポーネントが直接 API 呼び出し → データ取得重複・状態不整合。
- 単一巨大 Context → 任意の状態変更で全再レンダリング。

## 結果
- データ変更時はサマリだけ、フィルタ変更時はリストだけ再描画される。
- ファイル数は増えるが責務が明確で保守性が高い。
- 新規 UI 追加時は必ず container/ + presentation/ の 2 ファイルを作る規約とする。
