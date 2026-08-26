import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))
from night_shift_paths import resolve_data_home

ENTRYPOINT = ROOT / "bin" / "night-shift"
MAX_ENTRYPOINT_LINES = 120


class CliLayoutTests(unittest.TestCase):
    def test_night_shift_entrypoint_is_thin(self):
        lines = ENTRYPOINT.read_text(encoding="utf-8").splitlines()
        self.assertLess(
            len(lines),
            MAX_ENTRYPOINT_LINES,
            f"bin/night-shift should stay under {MAX_ENTRYPOINT_LINES} lines; found {len(lines)}",
        )
        text = "\n".join(lines)
        self.assertIn("from night_shift_cli import", text)
        self.assertIn("def main", Path(ROOT / "bin" / "night_shift_cli.py").read_text(encoding="utf-8"))

    def test_explicit_homes_win_over_xdg_and_legacy(self):
        with patch.dict(os.environ, {"NIGHTSHIFT_HOME": "/tmp/ns-home", "CODEX_HOME": "/tmp/codex-home", "XDG_DATA_HOME": "/tmp/xdg"}, clear=False):
            self.assertEqual(resolve_data_home(), Path("/tmp/ns-home"))
        env = {key: value for key, value in os.environ.items() if key != "NIGHTSHIFT_HOME"}
        env["CODEX_HOME"] = "/tmp/codex-home"
        env.pop("XDG_DATA_HOME", None)
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(resolve_data_home(), Path("/tmp/codex-home"))
        both = {key: value for key, value in os.environ.items() if key != "NIGHTSHIFT_HOME"}
        both["CODEX_HOME"] = "/tmp/codex-home"
        both["XDG_DATA_HOME"] = "/tmp/xdg"
        with patch.dict(os.environ, both, clear=True):
            self.assertEqual(resolve_data_home(), Path("/tmp/xdg/nightshift"))


if __name__ == "__main__":
    unittest.main()
