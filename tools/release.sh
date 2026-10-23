#!/usr/bin/env bash
# Cut a release: set the plugin version, test, commit and tag.
# Plugin users get changes only when this version changes.
# Write the "## X.Y.Z" section of CHANGELOG.md first.
# Usage: tools/release.sh X.Y.Z   then: git push origin main --tags
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${1:?usage: tools/release.sh X.Y.Z}"
cd "$ROOT"

[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "version must be X.Y.Z"; exit 1; }
[ "$(git branch --show-current)" = main ] || { echo "release from main"; exit 1; }
git rev-parse -q --verify "refs/tags/v$VERSION" >/dev/null && { echo "tag v$VERSION exists"; exit 1; }
grep -q "^## $VERSION" CHANGELOG.md || { echo "add a '## $VERSION' section to CHANGELOG.md first"; exit 1; }
[ -z "$(git status --porcelain | grep -v ' CHANGELOG.md$')" ] || { echo "commit your other changes first"; exit 1; }

python3 - "$VERSION" <<'PY'
import json, sys
path = ".claude-plugin/plugin.json"
data = json.load(open(path))
data["version"] = sys.argv[1]
open(path, "w").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
PY

if command -v claude >/dev/null; then claude plugin validate .; fi
tools/test-demo.sh >/dev/null
tools/build-zip.sh

git add .claude-plugin/plugin.json CHANGELOG.md
git commit -m "Release $VERSION"
git tag -a "v$VERSION" -m "dashboard-finanze $VERSION"
echo "tagged v$VERSION. Publish with: git push origin main --tags"
