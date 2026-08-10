#!/usr/bin/env bash
# Lint the whole repository without pre-commit (useful in CI or fresh checkouts).
# Requires: ruff (pip install -r requirements-dev.txt) and node.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> ruff (Python)"
ruff check .

echo "==> node --check (JavaScript)"
found=0
while IFS= read -r -d '' f; do
  node --check "$f"
  found=$((found + 1))
done < <(find georidge_platform -name '*.js' -print0)
echo "    checked $found JS files"

echo "All lint checks passed."
