#!/usr/bin/env bash
set -euo pipefail
input="$1"
gawk -f "$(dirname "$0")/checker.awk" "$input"
