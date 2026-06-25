#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

bash -n \
  install.sh \
  bin/maestro-smoke.sh \
  bin/maestro-delegate \
  bin/maestro-local \
  bin/maestro-windows \
  bin/maestro-claude

python3 -m py_compile \
  bin/night-shift \
  bin/maestro-token-report

version_file="$(tr -d '[:space:]' < VERSION)"
cli_version="$(python3 - <<'PY'
import ast
from pathlib import Path

module = ast.parse(Path("bin/night-shift").read_text(encoding="utf-8"))
for node in module.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "VERSION":
                print(ast.literal_eval(node.value))
                raise SystemExit(0)
raise SystemExit("VERSION constant not found in bin/night-shift")
PY
)"

if [[ "$version_file" != "$cli_version" ]]; then
  echo "VERSION mismatch: VERSION=$version_file bin/night-shift=$cli_version" >&2
  exit 1
fi

python3 bin/night-shift --version | grep -q "Night Shift $version_file"
python3 bin/night-shift --help >/dev/null
bin/night-shift --version | grep -q "Night Shift $version_file"
bin/night-shift --help >/dev/null

tmp_home="$(mktemp -d)"
trap 'rm -rf "$tmp_home"' EXIT
CODEX_HOME="$tmp_home" python3 bin/night-shift start --repo "$repo_root" --yes --dry-run --skip-smoke >/dev/null
CODEX_HOME="$tmp_home" python3 bin/night-shift start --repo "$repo_root" --yes --dry-run --skip-smoke >/dev/null
test -s "$tmp_home/night-shift/config.json"
find "$tmp_home/maestro/overnight" -path '*/lab/readiness.json' -type f | grep -q .

noninteractive_out="$tmp_home/noninteractive.out"
if CODEX_HOME="$tmp_home" python3 bin/night-shift start </dev/null >"$noninteractive_out" 2>&1; then
  echo "non-interactive start without --yes should fail" >&2
  exit 1
fi
grep -q "I need a keyboard" "$noninteractive_out"

for required in README.md CONTRIBUTING.md SAFETY.md LICENSE CHANGELOG.md PACKAGE.md VERSION; do
  if [[ ! -s "$required" ]]; then
    echo "missing or empty package file: $required" >&2
    exit 1
  fi
done

if ! grep -q "Private license placeholder" LICENSE; then
  echo "LICENSE must clearly state the current private placeholder status" >&2
  exit 1
fi

if ! grep -q "night-shift" PACKAGE.md; then
  echo "PACKAGE.md must name the public command" >&2
  exit 1
fi

echo "package checks passed"
