#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
usage: ./install.sh [--doctor REPO]

Installs Maestro Night Shift into:
  ${CODEX_HOME:-$HOME/.codex}/bin
  ${CODEX_HOME:-$HOME/.codex}/skills/maestro-overnight

Options:
  --doctor REPO   run maestro-nightshift doctor after installing
  -h, --help      show this help
EOF
}

doctor_repo=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --doctor)
      if [[ $# -lt 2 ]]; then
        echo "missing repo path after --doctor" >&2
        exit 2
      fi
      doctor_repo="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

codex_home="${CODEX_HOME:-$HOME/.codex}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bin_dir="$codex_home/bin"
skill_dir="$codex_home/skills/maestro-overnight"

for required in git python3 curl rsync; do
  if ! command -v "$required" >/dev/null 2>&1; then
    echo "missing required command: $required" >&2
    exit 1
  fi
done

mkdir -p "$bin_dir" "$skill_dir"

cp "$repo_root"/bin/maestro-* "$bin_dir/"
chmod +x "$bin_dir"/maestro-*

rsync -a --delete "$repo_root/skills/maestro-overnight/" "$skill_dir/"

echo "Maestro Night Shift installed."
echo "Installed command: $bin_dir/maestro-nightshift"

if [[ ":$PATH:" != *":$bin_dir:"* ]]; then
  echo
  echo "Add this to your shell profile if 'maestro-nightshift' is not found:"
  echo "  export PATH=\"$bin_dir:\$PATH\""
fi

echo
echo "Next:"
echo "  maestro-nightshift doctor --repo /path/to/project"
echo
echo "Optional compute to start before a real run:"
echo "  Mac local: open LM Studio, start the local server, and load a chat model."
echo "  Windows worker: set WINDOWS_WORKER_BASE_URL and WINDOWS_WORKER_MODEL if you have one."
echo "  Claude: install and sign in to the claude CLI if you want that reasoning lane."
echo "  GitHub: install gh and run 'gh auth login' if you want PR context."

if [[ -n "$doctor_repo" ]]; then
  echo
  "$bin_dir/maestro-nightshift" doctor --repo "$doctor_repo"
fi
