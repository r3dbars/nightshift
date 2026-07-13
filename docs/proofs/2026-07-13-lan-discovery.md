# LAN Model-Server Discovery Proof

This proof covers the opt-in discovery path used after a user chooses “this
Mac plus my other AI computer.” Discovery reads only existing ARP neighbors,
keeps private IPv4 addresses, probes the known model-list endpoints on ports
11434 and 1234, and does not include repository context.

## Live Mac Run

Command:

```bash
python3 - <<'PY'
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("night_shift_live", "bin/night-shift")
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = module
loader.exec_module(module)
print(module.discover_lan_workers())
PY
```

Result on 2026-07-13:

```text
LAN_DISCOVERY_LIVE: GREEN | http://192.168.7.201:11434/v1 | qwen3-coder:30b-32k
```

The worker was the configured private-LAN Windows Ollama endpoint. The probe
did not send a chat request or any repository data. The setup flow still asks
before saving a discovered endpoint; if discovery returns nothing, it offers
a manual address or a Mac-only run.

## Deterministic Tests

The full package gate passed with 373 tests. Its LAN tests cover private/public
address filtering, local-address exclusion, known-port model-list requests,
and bounded result selection.

This proof does not claim provider restart or Swift runner support. Those stay
open hardware gaps until they have direct evidence.
