#!/usr/bin/env bash
# Lambda パッケージ（api / worker 共通の zip）をビルドする。
# zip ルートに handlers/ services/ common/ が並ぶよう src/ の中身を配置する。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BE="$ROOT/backend"
BUILD="$BE/dist/build"
ZIP="$BE/dist/lambda.zip"

echo "==> clean"
rm -rf "$BE/dist"
mkdir -p "$BUILD"

echo "==> copy source"
cp -r "$BE/src/." "$BUILD/"

echo "==> pip install deps"
if [ -s "$BE/requirements.txt" ]; then
  python3 -m pip install -r "$BE/requirements.txt" -t "$BUILD" --quiet \
    --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 \
    --only-binary=:all: --upgrade 2>/dev/null || \
  python3 -m pip install -r "$BE/requirements.txt" -t "$BUILD" --quiet
fi

echo "==> remove caches"
find "$BUILD" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find "$BUILD" -type d -name "*.dist-info" -prune -exec rm -rf {} + 2>/dev/null || true

echo "==> zip"
(cd "$BUILD" && zip -qr "$ZIP" .)
echo "==> built: $ZIP ($(du -h "$ZIP" | cut -f1))"
