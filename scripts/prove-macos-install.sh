#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_home="$(mktemp -d -t night-shift-macos-install.XXXXXX)"
trap 'rm -rf "$tmp_home"' EXIT

codex_home="$tmp_home/.codex"
mkdir -p "$tmp_home"

HOME="$tmp_home" SHELL=/bin/zsh "$repo_root/install.sh" --codex-home "$codex_home" >/dev/null
test -x "$codex_home/bin/night-shift"
test -L "$codex_home/skills/night-shift" || test -d "$codex_home/skills/night-shift"
test -s "$tmp_home/.zshrc"
grep -Fqx "export PATH=\"$codex_home/bin:\$PATH\"" "$tmp_home/.zshrc"

HOME="$tmp_home" SHELL=/bin/zsh zsh -ic 'command -v night-shift && night-shift --version' \
  >/tmp/night-shift-macos-version 2>/dev/null
grep -Fxq "$codex_home/bin/night-shift" /tmp/night-shift-macos-version
grep -Eq '^Night Shift [0-9]+[.][0-9]+[.][0-9]+$' /tmp/night-shift-macos-version

config_home="$tmp_home/config-home"
HOME="$config_home" SHELL=/bin/zsh CODEX_HOME="$config_home/.codex" \
  "$repo_root/install.sh" --codex-home "$config_home/.codex" --no-path >/dev/null
HOME="$config_home" CODEX_HOME="$config_home/.codex" \
  "$config_home/.codex/bin/night-shift" start --repo "$repo_root" --yes --setup-only --skip-smoke >/tmp/night-shift-macos-setup
grep -Fq 'NIGHTSHIFT_START: GREEN' /tmp/night-shift-macos-setup
test -s "$config_home/.codex/night-shift/config.json"

HOME="$tmp_home" SHELL=/bin/zsh "$repo_root/install.sh" --codex-home "$codex_home" >/dev/null
test "$(grep -Fxc "export PATH=\"$codex_home/bin:\$PATH\"" "$tmp_home/.zshrc")" -eq 1

echo "MACOS_INSTALL_PROOF: GREEN | clean temporary macOS home installed Night Shift, resolved it from a new zsh, and completed first-run setup"
