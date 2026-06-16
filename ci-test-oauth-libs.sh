#!/usr/bin/env bash
set -euo pipefail

for config in extensions.default.json extensions.php8.6.json; do
    jq -e '.[] | select(.name == "oauth") | .libs | split(" ") | index("nghttp2")' "$config" >/dev/null
done
