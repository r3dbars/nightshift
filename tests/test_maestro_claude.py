import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAESTRO_CLAUDE = ROOT / "bin" / "maestro-claude"

REQUIRED_FLAGS = (
    "claude -p",
    "--permission-mode plan",
    "--tools Read",
    "--no-session-persistence",
    "--safe-mode",
)


class MaestroClaudeSandboxTests(unittest.TestCase):
    def test_handoff_aligned_sandbox_flags_are_present(self):
        script = MAESTRO_CLAUDE.read_text(encoding="utf-8")
        for flag in REQUIRED_FLAGS:
            with self.subTest(flag=flag):
                self.assertIn(flag, script)
        self.assertIn("NIGHTSHIFT_HOME", script)
        self.assertIn(".local", script)
        self.assertNotIn('Path.home() / ".codex")', script)


if __name__ == "__main__":
    unittest.main()
