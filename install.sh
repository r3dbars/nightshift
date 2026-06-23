#!/usr/bin/env bash
set -euo pipefail

codex_home="${CODEX_HOME:-$HOME/.codex}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$codex_home/bin"
mkdir -p "$codex_home/skills/maestro-overnight"

cp "$repo_root"/bin/maestro-* "$codex_home/bin/"
chmod +x "$codex_home"/bin/maestro-*

rsync -a --delete "$repo_root/skills/maestro-overnight/" "$codex_home/skills/maestro-overnight/"

echo "Maestro Night Shift installed."
echo "Try: maestro-nightshift doctor --repo /path/to/project"

