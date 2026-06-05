# frontend

入力支援 SPA / AI チューニング画面（React + TypeScript + Vite）。

設計は [../doc/design/frontend-architecture.md](../doc/design/frontend-architecture.md) を参照。

## セットアップ

```bash
npm install
cp .env.example .env      # モックファースト（VITE_USE_MOCK=true）で起動可能
npm run dev               # http://localhost:3000
```

## スクリプト

| コマンド | 内容 |
|---|---|
| `npm run dev` | 開発サーバー |
| `npm run build` | 型チェック + ビルド |
| `npm run lint` | ESLint |
| `npm run type-check` | tsc --noEmit |

## 構成

```
src/
├── app/         App.tsx, routes.tsx
├── pages/       レイアウト専用
├── features/    auth / input-assist / admin
├── shared/      components/ providers/ hooks/ api/ types/ config/ mocks/ lib/
├── layouts/
└── routes/
```

各コンポーネントは `container/` + `presentation/`（1:1）で構成する（[ADR-006](../doc/adr/006-frontend-container-presentation.md)）。

## ステータス

Phase 1（確認支援）はヘッドレスのため、フロントは土台のみ。
入力支援は Phase 3、AI チューニング画面は Phase 2 で実装。
