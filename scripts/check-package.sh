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
  bin/night_shift_*.py \
  bin/maestro-token-report

python3 -m unittest discover -s tests -p 'test_*.py'

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
copied_home="$tmp_home/copied-install"
./install.sh --codex-home "$copied_home" >/dev/null
"$copied_home/bin/night-shift" --version | grep -q "Night Shift $version_file"

CODEX_HOME="$tmp_home" python3 bin/night-shift start --repo "$repo_root" --yes --setup-only --skip-smoke >/dev/null
test -s "$tmp_home/night-shift/config.json"
find "$tmp_home/maestro/overnight" -path '*/lab/readiness.json' -type f | grep -q .
config_before="$(shasum -a 256 "$tmp_home/night-shift/config.json")"
ledgers_before="$(find "$tmp_home/maestro/overnight" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
CODEX_HOME="$tmp_home" python3 bin/night-shift start --repo "$repo_root" --yes --dry-run --skip-smoke >/dev/null
test "$config_before" = "$(shasum -a 256 "$tmp_home/night-shift/config.json")"
test "$ledgers_before" = "$(find "$tmp_home/maestro/overnight" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
mkdir "$tmp_home/not-a-repo"
if CODEX_HOME="$tmp_home" python3 bin/night-shift start --repo "$tmp_home/not-a-repo" --yes --setup-only >/dev/null; then
  echo "setup-only accepted a non-git directory" >&2
  exit 1
fi
test "$config_before" = "$(shasum -a 256 "$tmp_home/night-shift/config.json")"

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

if ! grep -q "MIT License" LICENSE; then
  echo "LICENSE must contain the MIT License" >&2
  exit 1
fi

if ! grep -q "night-shift" PACKAGE.md; then
  echo "PACKAGE.md must name the public command" >&2
  exit 1
fi

echo "package checks passed"
