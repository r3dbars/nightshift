# Hardware Scan Reference

The full playbook behind Step 3 of the First Night flow, and behind any
Tune-Up ("I got a new GPU", "add my other computer"). Everything here is
detect-then-confirm: run read-only probes with the user's consent, translate
the results into plain language, and only then ask what a command cannot
answer.

Consent rule: name what you are about to check ("a few read-only checks on
this machine — chip, memory, and whether a model server is running") before
running the probes. Never install, download, or start anything without an
explicit yes for that specific action.

## Probes

All probes are read-only. Use short timeouts so a missing server never stalls
the conversation.

### The machine itself

macOS:

```bash
sysctl -n machdep.cpu.brand_string                     # "Apple M3 Max"
echo "$(( $(sysctl -n hw.memsize) / 1073741824 )) GB"  # unified memory
pmset -g batt 2>/dev/null | head -1                     # battery vs AC power
```

Linux / WSL:

```bash
grep -m1 "model name" /proc/cpuinfo
free -g | awk '/^Mem:/ {print $2 " GB RAM"}'
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null
```

On Apple Silicon, unified memory is the number that matters: the GPU can use
almost all of it for model weights. Say that plainly — many users do not know
their MacBook is a capable inference box.

### Running model servers

```bash
curl -s --max-time 2 http://localhost:1234/v1/models     # LM Studio
curl -s --max-time 2 http://localhost:11434/api/tags     # Ollama
curl -s --max-time 2 http://localhost:8080/v1/models     # llama.cpp server (llama-server)
```

A JSON reply means the lane is live right now. Parse the model list out of it
rather than asking the user what is loaded.

### Installed but not running

```bash
command -v ollama >/dev/null 2>&1 && ollama list
ls /Applications 2>/dev/null | grep -i "lm studio"
command -v llama-server 2>/dev/null
python3 -c "import mlx_lm" 2>/dev/null && echo "mlx-lm installed"
```

If installed-but-stopped, offer the one-line fix immediately:

- Ollama: `ollama serve` (or just run any `ollama` command; the app usually
  autostarts it).
- LM Studio: open the app, load a model, start the server from the Developer
  tab (default port 1234).

## Reading the results

Capability tiers for quantized local models. Round in the user's favor but do
not overpromise:

| Memory (unified or VRAM) | Comfortable overnight models | Overnight role |
| --- | --- | --- |
| under 8 GB | 1–3B | light triage only; keep loops small |
| 8–16 GB | 3–8B | classification, TODO mining, summaries |
| 16–32 GB | 7–14B | solid repo analysts, review notes |
| 32–64 GB unified / 24 GB VRAM | 14B–32B | real drafting and patch plans; RTX 3090/4090 class |
| 96 GB+ unified / 48 GB+ VRAM | 70B-class quantized | deep review drafts |

Model picking, in order:

1. The largest **coder** model already downloaded (`qwen3-coder`,
   `qwen2.5-coder`, `deepseek-coder`, `codellama`).
2. Otherwise the largest **instruct/chat** model (`*-instruct`, `llama3*`,
   `phi-4`, `gemma*`, `mistral*`).
3. Never an embedding model (`nomic-embed*`, `*-embed*`, `bge-*`) and never a
   base (non-instruct) model.
4. If the hardware comfortably fits a bigger tier than anything downloaded,
   say so and offer the pull as a choice, sized honestly
   ("`ollama pull qwen3-coder:30b` — about a 19 GB download"). Do not start
   the download without a yes.

## Wiring the findings into the CLI

Both servers speak the OpenAI-compatible API, so they plug straight into the
existing flags:

| Found | Flags |
| --- | --- |
| Ollama on this machine | `--local-url http://localhost:11434/v1 --local-model <name>` |
| LM Studio on this machine | `--local-url http://localhost:1234/v1 --local-model <loaded model>` |
| llama.cpp server | `--local-url http://localhost:8080/v1 --local-model <name>` |
| Second machine on the LAN | `--windows-url http://<host>:11434/v1 --windows-model <name>` |

Persist without launching: add `--yes --setup-only` to `night-shift start`.

## Second machine on the network (the Windows GPU box)

The classic setup: a Mac as the coordinator, a Windows gaming PC as the heavy
draft lane. Ollama on Windows binds to localhost only by default, so it needs
two changes to serve the LAN:

On the Windows box:

1. Set the bind address: System Environment Variables → add
   `OLLAMA_HOST` = `0.0.0.0` (or in PowerShell: `setx OLLAMA_HOST 0.0.0.0`),
   then quit and restart Ollama.
2. Allow inbound TCP 11434 in Windows Defender Firewall, scoped to
   **private** networks only. Never expose the port on a public profile.
3. Pull a model sized to the GPU: for a 24 GB card,
   `ollama pull qwen3-coder:30b`.

Then verify from the coordinator machine:

```bash
curl -s --max-time 3 http://<windows-host>:11434/api/tags
```

When the user chooses **Mac plus my other AI computer** in the advanced setup,
Night Shift first checks only the private devices already present in the Mac's
ARP table. It asks only the known Ollama (`11434`) and LM Studio
(`1234`) model-list endpoints, with a small host limit and short time bound.
It sends no repository content, never scans public addresses, and asks the user
to confirm a match before saving it. If no match is found, the wizard offers a
manual address or lets the user continue Mac-only. Discovery is read-only and
never starts, installs, or changes software on the other computer.

Find the host: use the machine name (`<name>.local` often resolves on a home
LAN) or the IPv4 from `ipconfig` on the Windows box. If the curl times out,
check in this order: Ollama restarted after setting `OLLAMA_HOST`, firewall
rule active, both machines on the same network, no VPN swallowing LAN
traffic.

LM Studio on Windows works too: enable "Serve on Local Network" in its server
settings, then use `--windows-url http://<host>:1234/v1`.

If the second machine cannot be verified right now, save it as "add later"
and move on — onboarding never stalls on a powered-off PC. It can be wired in
any evening via Tune-Up.

## When nothing is found

Not a failure state. Offer, in this order:

1. **Install Ollama** (simplest path): macOS `brew install ollama` or the
   download from ollama.com; then `ollama pull` a model sized to the tier
   table above. With consent, do this for the user and verify with
   `ollama list`.
2. **Install LM Studio** (friendliest GUI): point them at lmstudio.ai; its
   built-in browser handles model selection.
3. **Run without local models tonight**: `night-shift start` still produces a
   repo scan and planning brief, and `night-shift doctor --repo <repo>` lists
   exact blockers. Say this plainly so nobody feels gated.

## Scan troubleshooting

- `curl` replies but the models list is empty: the server is up with no model
  loaded. LM Studio: load a model in the app. Ollama: `ollama pull <model>`.
- `ollama list` works but `curl localhost:11434` fails: the CLI exists but
  the server is not running — `ollama serve`.
- Apple Silicon reports plenty of memory but models run slowly: check the
  machine is not in Low Power Mode and is on AC power (`pmset -g batt`).
- Two servers running at once: prefer the one with the better model per the
  picking rules; mention the other exists.
- `night-shift doctor --repo <repo>` is the deeper readiness check (repo
  state, write permissions, power) once endpoints are chosen.
