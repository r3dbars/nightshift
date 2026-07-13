#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime="${CONTAINER_RUNTIME:-docker}"
image="${NIGHT_SHIFT_LINUX_IMAGE:-ubuntu:24.04}"

command -v "$runtime" >/dev/null 2>&1 || {
  echo "missing container runtime: $runtime" >&2
  exit 1
}

"$runtime" run --rm \
  --mount "type=bind,source=$repo_root,target=/src,readonly" \
  "$image" \
  bash -ceu '
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl git python3 rsync >/dev/null
    useradd --create-home --shell /bin/bash newcomer
    chown newcomer:newcomer /home/newcomer
    su newcomer -c "HOME=/home/newcomer SHELL=/bin/bash /src/install.sh"
    test "$(grep -Fxc '\''export PATH="/home/newcomer/.codex/bin:$PATH"'\'' /home/newcomer/.bashrc)" -eq 1
    su newcomer -c "HOME=/home/newcomer SHELL=/bin/bash bash -ic '\''command -v night-shift && night-shift --version'\''" \
      2>/dev/null | tee /tmp/night-shift-version
    grep -Fxq /home/newcomer/.codex/bin/night-shift /tmp/night-shift-version
    grep -Eq "^Night Shift [0-9]+[.][0-9]+[.][0-9]+$" /tmp/night-shift-version
    su newcomer -c "HOME=/home/newcomer bash -ceu '\''
      mkdir /home/newcomer/project
      cd /home/newcomer/project
      git init -q
      git config user.email newcomer@example.invalid
      git config user.name Newcomer
      printf \"print(42)\\n\" > app.py
      git add app.py
      git commit -qm initial
    '\''"
    su newcomer -c "HOME=/home/newcomer SHELL=/bin/bash bash -ic '\''
      night-shift start --repo /home/newcomer/project --yes --setup-only --skip-smoke
    '\''" 2>/dev/null | tee /tmp/night-shift-setup
    test -s /home/newcomer/.codex/night-shift/config.json
    grep -Fq "NIGHTSHIFT_START: GREEN" /tmp/night-shift-setup
    echo "LINUX_INSTALL_PROOF: GREEN | fresh Ubuntu user installed Night Shift, launched it from a new shell, and completed first-run setup"
  '
