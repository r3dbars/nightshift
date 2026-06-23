#!/usr/bin/env bash
set -u

echo "== Codex lane =="
git --version || true
gh --version | sed -n '1,2p' || true

echo
echo "== Claude CLI lane =="
if command -v claude >/dev/null 2>&1; then
  claude -p "Reply with exactly this and nothing else: MAESTRO_CLAUDE_OK" || true
else
  echo "claude not found"
fi

echo
echo "== Local LM Studio lane =="
MAESTRO_LOCAL_BASE_URL="${MAESTRO_LOCAL_BASE_URL:-http://localhost:1234/v1}"
MAESTRO_LOCAL_MODEL="${MAESTRO_LOCAL_MODEL:-phi-4-mini-instruct}"
if curl -fsS "$MAESTRO_LOCAL_BASE_URL/models" >/tmp/maestro-local-models.json 2>/tmp/maestro-local-error.txt; then
  python3 - <<'PY'
import json
print([m["id"] for m in json.load(open("/tmp/maestro-local-models.json"))["data"]])
PY
  curl -s "$MAESTRO_LOCAL_BASE_URL/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$MAESTRO_LOCAL_MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly: MAESTRO_LOCAL_OK\"}],\"max_tokens\":30}" \
    | python3 -c 'import sys,json; print(json.load(sys.stdin)["choices"][0]["message"]["content"].strip())' || true
else
  echo "LM Studio server not reachable at $MAESTRO_LOCAL_BASE_URL"
  cat /tmp/maestro-local-error.txt
fi

echo
echo "== Windows worker lane =="
WINDOWS_WORKER_BASE_URL="${WINDOWS_WORKER_BASE_URL:-}"
WINDOWS_WORKER_MODEL="${WINDOWS_WORKER_MODEL:-qwen3-coder:30b}"
WINDOWS_WORKER_API_KEY="${WINDOWS_WORKER_API_KEY:-ollama}"

if [ -z "$WINDOWS_WORKER_BASE_URL" ]; then
  echo "Windows worker not configured. Set WINDOWS_WORKER_BASE_URL to enable this lane."
elif curl -fsS "$WINDOWS_WORKER_BASE_URL/models" \
  -H "Authorization: Bearer $WINDOWS_WORKER_API_KEY" \
  >/tmp/maestro-windows-models.json 2>/tmp/maestro-windows-error.txt; then
  python3 - <<'PY'
import json
print([m.get("id") for m in json.load(open("/tmp/maestro-windows-models.json")).get("data", [])])
PY
  curl -s "$WINDOWS_WORKER_BASE_URL/chat/completions" \
    -H "Authorization: Bearer $WINDOWS_WORKER_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$WINDOWS_WORKER_MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly: MAESTRO_WINDOWS_OK\"}],\"max_tokens\":30}" \
    | python3 -c 'import sys,json; data=json.load(sys.stdin); print(data["choices"][0]["message"]["content"].strip() if "choices" in data else data)' || true
else
  echo "Windows worker not reachable at $WINDOWS_WORKER_BASE_URL"
  cat /tmp/maestro-windows-error.txt
fi
