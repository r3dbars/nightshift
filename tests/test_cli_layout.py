import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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


if __name__ == "__main__":
    unittest.main()
