#!/usr/bin/env bash
# tools のテストをまとめて動かす。
set -euo pipefail
cd "$(dirname "$0")"
echo "== analyze.py（合成した音で特徴の大小を確かめる）"
uv run -q --script test_analyze.py
echo "== gxpatch.py（見本のパッチで読み書きを確かめる）"
uv run -q --script test_gxpatch.py
