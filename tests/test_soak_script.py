import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SoakScriptTests(unittest.TestCase):
    def test_short_rehearsal_persists_proof_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            proof = Path(tmp) / "proof.json"
            environment = {
                **os.environ,
                "NIGHT_SHIFT_SOAK_SECONDS": "2",
                "NIGHT_SHIFT_SOAK_KILL_AFTER_SECONDS": "1",
                "NIGHT_SHIFT_SOAK_INTERVAL_SECONDS": "1",
                "NIGHT_SHIFT_SOAK_PROOF_PATH": str(proof),
            }
            result = subprocess.run(
                ["bash", str(ROOT / "scripts" / "prove-ten-hour-soak.sh")],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                timeout=90,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("TEN_HOUR_SOAK_PROOF: GREEN", result.stdout)
            payload = json.loads(proof.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "GREEN")
            self.assertEqual(payload["duration_seconds"], 2)
            self.assertEqual(payload["active_state_remaining"], False)
            self.assertGreaterEqual(payload["crash_recoveries"], payload["controllers_killed"])


if __name__ == "__main__":
    unittest.main()
