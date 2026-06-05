import { createBrowserRouter } from 'react-router-dom'

// Phase 1 では確認支援（ServiceNow ヘッドレス）が中心のため、画面は土台のみ。
// Phase 3 で入力支援 SPA、Phase 2 で AI チューニング画面を追加する。
export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <main className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
          <h1 className="text-xl font-semibold text-gray-900">aws-rag-poc</h1>
          <p className="mt-2 text-sm text-gray-500">
            フロント土台。入力支援 / AI チューニング画面は後続フェーズで実装。
          </p>
        </div>
      </main>
    ),
  },
])
