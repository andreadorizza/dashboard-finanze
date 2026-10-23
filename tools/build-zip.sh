#!/usr/bin/env bash
# Build dist/dashboard-finanze.zip with the skill folder at the zip's root,
# the shape claude.ai's "Upload a skill" expects.
# Usage: tools/build-zip.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME=dashboard-finanze
mkdir -p "$ROOT/dist"
rm -f "$ROOT/dist/$NAME.zip"
cd "$ROOT/skills"
zip -qr "$ROOT/dist/$NAME.zip" "$NAME" -x '*/__pycache__/*' '*.pyc' '*/.DS_Store'
echo "built dist/$NAME.zip ($(du -h "$ROOT/dist/$NAME.zip" | cut -f1))"
