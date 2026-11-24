#!/bin/bash
# Builds wp-community-data.zip, the file people upload to Claude or hand to their agent.
# Usage: bash skill/build-zip.sh [output-dir]   (default ~/Downloads)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
out="${1:-$HOME/Downloads}"
rm -f "$out/wp-community-data.zip"
cd "$here" && zip -qr -X "$out/wp-community-data.zip" wp-community-data -x '*/__pycache__/*' '*.DS_Store'
echo "$out/wp-community-data.zip"
