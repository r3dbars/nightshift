#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_home="$(mktemp -d -t night-shift-blank-home.XXXXXX)"
trap 'rm -rf "$tmp_home"' EXIT

mkdir -p "$tmp_home/work" "$tmp_home/gh"
set +e
(
  cd "$tmp_home/work"
  HOME="$tmp_home" CODEX_HOME="$tmp_home/.codex" GH_CONFIG_DIR="$tmp_home/gh" \
    "$repo_root/bin/night-shift" start --yes --setup-only --skip-smoke
) >"$tmp_home/output" 2>&1
rc=$?
set -e

if [ "$rc" -ne 2 ] || ! grep -Fq "I could not find a project yet" "$tmp_home/output"; then
  cat "$tmp_home/output" >&2
  echo "blank-home recovery returned an unexpected result: rc=$rc" >&2
  exit 1
fi
if [ -e "$tmp_home/.codex/night-shift/config.json" ]; then
  echo "blank-home recovery saved setup without a project" >&2
  exit 1
fi

echo "BLANK_HOME_RECOVERY_PROOF: GREEN | clear repo/GitHub next steps and no setup saved without an eligible project"
