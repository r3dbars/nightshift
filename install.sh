#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
usage: ./install.sh [--prefix PATH] [--codex-home PATH] [--link] [--no-path] [--doctor REPO]

Installs Night Shift into:
  $prefix/bin
  $prefix/skills/night-shift

Default prefix, first match wins:
  $NIGHTSHIFT_HOME
  $XDG_DATA_HOME/nightshift
  $HOME/.local/share/nightshift
  $CODEX_HOME   (fallback for existing Codex-home installs)

Options:
  --prefix PATH      install under PATH (does not require ~/.codex)
  --codex-home PATH  legacy alias for --prefix; install under PATH
  --link             symlink bin files and the skill to this checkout for development
  --no-path          do not add the Night Shift command directory to your shell profile
  --doctor REPO      run night-shift doctor after installing
  -h, --help         show this help
EOF
}

default_prefix() {
  if [[ -n "${NIGHTSHIFT_HOME:-}" ]]; then
    printf '%s\n' "${NIGHTSHIFT_HOME/#\~/$HOME}"
    return
  fi
  if [[ -n "${XDG_DATA_HOME:-}" ]]; then
    printf '%s\n' "${XDG_DATA_HOME/#\~/$HOME}/nightshift"
    return
  fi
  if [[ -n "${CODEX_HOME:-}" ]]; then
    printf '%s\n' "${CODEX_HOME/#\~/$HOME}"
    return
  fi
  printf '%s\n' "$HOME/.local/share/nightshift"
}

doctor_repo=""
link_install=0
configure_path=1
prefix=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix|--codex-home)
      if [[ $# -lt 2 ]]; then
        echo "missing path after $1" >&2
        exit 2
      fi
      prefix="$2"
      shift 2
      ;;
    --link)
      link_install=1
      shift
      ;;
    --no-path)
      configure_path=0
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

if [[ -z "$prefix" ]]; then
  prefix="$(default_prefix)"
fi
prefix="${prefix/#\~/$HOME}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bin_dir="$prefix/bin"
skill_dir="$prefix/skills/night-shift"
runner_dir="$prefix/containers/runner"

shell_profile=""
case "${SHELL:-}" in
  */zsh) shell_profile="$HOME/.zshrc" ;;
  */bash) shell_profile="$HOME/.bashrc" ;;
esac
if [[ -z "$shell_profile" ]]; then
  shell_profile="$HOME/.profile"
fi

path_start="# Night Shift command"
path_line="export PATH=\"$bin_dir:\$PATH\""

configure_shell_path() {
  if [[ ":$PATH:" == *":$bin_dir:"* ]]; then
    return 0
  fi
  if [[ "$configure_path" -eq 0 ]]; then
    return 0
  fi
  if [[ -L "$shell_profile" ]]; then
    echo "refusing to edit symlinked shell profile: $shell_profile" >&2
    return 1
  fi
  touch "$shell_profile"
  if ! grep -Fqx "$path_line" "$shell_profile"; then
    printf '\n%s\n%s\n' "$path_start" "$path_line" >> "$shell_profile"
  fi
}

for required in git python3 curl rsync; do
  if ! command -v "$required" >/dev/null 2>&1; then
    echo "missing required command: $required" >&2
    exit 1
  fi
done

mkdir -p "$bin_dir" "$prefix/skills" "$prefix/containers"

install_python_modules() {
  local target_bin="$1"
  local mode="$2"
  if [[ "$mode" == "link" ]]; then
    for source in "$repo_root"/bin/night_shift_*.py; do
      target="$target_bin/$(basename "$source")"
      rm -f "$target"
      ln -s "$source" "$target"
    done
    if [[ -d "$repo_root/bin/night_shift_commands" ]]; then
      rm -rf "$target_bin/night_shift_commands"
      ln -s "$repo_root/bin/night_shift_commands" "$target_bin/night_shift_commands"
    fi
  else
    cp "$repo_root"/bin/night_shift_*.py "$target_bin/"
    if [[ -d "$repo_root/bin/night_shift_commands" ]]; then
      rm -rf "$target_bin/night_shift_commands"
      mkdir -p "$target_bin/night_shift_commands"
      rsync -a --delete "$repo_root/bin/night_shift_commands/" "$target_bin/night_shift_commands/"
    fi
  fi
}

if [[ "$link_install" -eq 1 ]]; then
  for source in "$repo_root"/bin/maestro-* "$repo_root/bin/night-shift"; do
    target="$bin_dir/$(basename "$source")"
    rm -f "$target"
    ln -s "$source" "$target"
  done
  install_python_modules "$bin_dir" "link"

  rm -rf "$skill_dir"
  ln -s "$repo_root/skills/night-shift" "$skill_dir"
  rm -rf "$runner_dir"
  ln -s "$repo_root/containers/runner" "$runner_dir"
else
  mkdir -p "$skill_dir" "$runner_dir"
  cp "$repo_root"/bin/maestro-* "$repo_root/bin/night-shift" "$bin_dir/"
  chmod +x "$bin_dir"/maestro-* "$bin_dir/night-shift"
  install_python_modules "$bin_dir" "copy"

  rsync -a --delete "$repo_root/skills/night-shift/" "$skill_dir/"
  rsync -a --delete "$repo_root/containers/runner/" "$runner_dir/"
fi

echo "Night Shift installed."
if [[ "$link_install" -eq 1 ]]; then
  echo "Install mode: linked to $repo_root"
fi
echo "Installed path: $prefix"
echo "Installed command: $bin_dir/night-shift"
"$bin_dir/night-shift" --version

if [[ ":$PATH:" != *":$bin_dir:"* ]]; then
  path_configured=0
  if configure_shell_path; then
    path_configured="$configure_path"
  else
    echo "PATH setup skipped for safety. Your install is still ready." >&2
  fi
  if [[ "$path_configured" -eq 1 ]]; then
    echo "Command added to $shell_profile."
    echo "Open a new terminal, or run this once now:"
  else
    echo "PATH setup skipped. Run this once in each terminal:"
  fi
  echo "  export PATH=\"$bin_dir:\$PATH\""
fi

echo
echo "Next:"
if [[ ":$PATH:" == *":$bin_dir:"* ]]; then
  echo "  night-shift start"
else
  echo "  $bin_dir/night-shift start"
fi
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
