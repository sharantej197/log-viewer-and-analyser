#!/usr/bin/env bash
set -euo pipefail
input="$1"
output="$2"
original="$3"
gawk -f "$(dirname "$0")/tablemaker.awk" "$input" > "$output"
cp "$output" "$original"
