#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
usage: ./install.sh [--codex-home PATH] [--link] [--doctor REPO]

Installs Night Shift into:
  ${CODEX_HOME:-$HOME/.codex}/bin
  ${CODEX_HOME:-$HOME/.codex}/skills/night-shift

Options:
  --codex-home PATH  install under PATH instead of ${CODEX_HOME:-$HOME/.codex}
  --link             symlink bin files and the skill to this checkout for development
  --doctor REPO   run night-shift doctor after installing
  -h, --help      show this help
EOF
}

doctor_repo=""
link_install=0
codex_home="${CODEX_HOME:-$HOME/.codex}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --codex-home)
      if [[ $# -lt 2 ]]; then
        echo "missing path after --codex-home" >&2
        exit 2
      fi
      codex_home="$2"
      shift 2
      ;;
    --link)
      link_install=1
      shift
      ;;
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

codex_home="${codex_home/#\~/$HOME}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bin_dir="$codex_home/bin"
skill_dir="$codex_home/skills/night-shift"

shell_profile=""
case "${SHELL:-}" in
  */zsh) shell_profile="$HOME/.zshrc" ;;
  */bash) shell_profile="$HOME/.bashrc" ;;
esac
if [[ -z "$shell_profile" ]]; then
  shell_profile="$HOME/.profile"
fi

for required in git python3 curl rsync; do
  if ! command -v "$required" >/dev/null 2>&1; then
    echo "missing required command: $required" >&2
    exit 1
  fi
done

mkdir -p "$bin_dir" "$codex_home/skills"

if [[ "$link_install" -eq 1 ]]; then
  for source in "$repo_root"/bin/maestro-* "$repo_root/bin/night-shift"; do
    target="$bin_dir/$(basename "$source")"
    rm -f "$target"
    ln -s "$source" "$target"
  done

  rm -rf "$skill_dir"
  ln -s "$repo_root/skills/night-shift" "$skill_dir"
else
  mkdir -p "$skill_dir"
  cp "$repo_root"/bin/maestro-* "$repo_root/bin/night-shift" "$bin_dir/"
  chmod +x "$bin_dir"/maestro-* "$bin_dir/night-shift"

  rsync -a --delete "$repo_root/skills/night-shift/" "$skill_dir/"
fi

echo "Night Shift installed."
if [[ "$link_install" -eq 1 ]]; then
  echo "Install mode: linked to $repo_root"
fi
echo "Installed command: $bin_dir/night-shift"
"$bin_dir/night-shift" --version

if [[ ":$PATH:" != *":$bin_dir:"* ]]; then
  echo
  echo "Use it in this terminal now:"
  echo "  export PATH=\"$bin_dir:\$PATH\""
  echo
  echo "Make that permanent:"
  echo "  printf '%s\n' 'export PATH=\"$bin_dir:\$PATH\"' >> \"$shell_profile\""
  echo
  echo "Or skip PATH setup and run it directly:"
  echo "  $bin_dir/night-shift doctor --repo /path/to/project"
fi

echo
echo "Next:"
echo "  night-shift doctor --repo /path/to/project"
echo
echo "Optional compute to start before a real run:"
echo "  Mac local: open LM Studio, start the local server, and load phi-4-mini-instruct."
echo "  Windows worker: export WINDOWS_WORKER_BASE_URL=http://WINDOWS_HOST:11434/v1"
echo "                  export WINDOWS_WORKER_MODEL=qwen3-coder:30b"
echo "  Claude: install and sign in to the claude CLI if you want that reasoning lane."
echo "  GitHub: install gh and run 'gh auth login' if you want PR context."

if [[ -n "$doctor_repo" ]]; then
  echo
  "$bin_dir/night-shift" doctor --repo "$doctor_repo"
fi
