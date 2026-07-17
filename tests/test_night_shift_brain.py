import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_brain import run_brain_intake


class BrainIntakeTests(unittest.TestCase):
    def make_vault(self, root: Path) -> Path:
        vault = root / "claudebrain"
        (vault / "raw" / "dictations").mkdir(parents=True)
        (vault / "raw" / "README.md").write_text("protected\n", encoding="utf-8")
        (vault / "CLAUDE.md").write_text("local constitution\n", encoding="utf-8")
        return vault

    def test_triages_new_raw_file_into_one_source_linked_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = self.make_vault(Path(tmp))
            source = vault / "raw" / "dictations" / "today.md"
            source.write_text("We decided to ship the Transcripted beta next week.\n", encoding="utf-8")
            calls = []

            def model(prompt, model):
                calls.append((prompt, model))
                return json.dumps({
                    "classification": "A",
                    "summary": "The source records a beta shipping decision.",
                    "people": [],
                    "projects": ["Transcripted"],
                    "commitments": ["ship the beta next week"],
                    "evidence_quotes": ["We decided to ship the Transcripted beta next week."],
                    "durable_signal": True,
                })

            result = run_brain_intake(
                vault,
                state_path=Path(tmp) / "state.json",
                local_model="local-model",
                max_files=25,
                max_chars=12000,
                max_bytes=200000,
                include_legacy=False,
                call_model=model,
                generated_at="2026-07-16T02:00:00+00:00",
            )
            self.assertEqual(result["status"], "GREEN")
            self.assertEqual(result["processed"], 1)
            self.assertEqual(len(calls), 1)
            packet = Path(result["packet"]).read_text(encoding="utf-8")
            self.assertIn("raw/dictations/today.md", packet)
            self.assertIn("The source records a beta shipping decision.", packet)
            self.assertIn("We decided to ship the Transcripted beta next week.", packet)

    def test_invalid_local_output_stays_hold_and_is_retryable(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = self.make_vault(Path(tmp))
            source = vault / "raw" / "note.md"
            source.write_text("ambiguous note\n", encoding="utf-8")
            result = run_brain_intake(
                vault,
                state_path=Path(tmp) / "state.json",
                local_model="local-model",
                max_files=25,
                max_chars=12000,
                max_bytes=200000,
                include_legacy=False,
                call_model=lambda _prompt, _model: "not json",
                generated_at="2026-07-16T02:00:00+00:00",
            )
            self.assertEqual(result["status"], "YELLOW")
            self.assertEqual(result["blocked"], 1)
            state = json.loads((Path(tmp) / "state.json").read_text(encoding="utf-8"))
            self.assertNotIn("raw/note.md", state["files"])
            self.assertIn("MODEL_INVALID", Path(result["packet"]).read_text(encoding="utf-8"))

    def test_own_packets_protected_files_and_unchanged_sources_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = self.make_vault(Path(tmp))
            (vault / "raw" / "night-shift-raw-intake-old.md").write_text("old packet\n", encoding="utf-8")
            (vault / "raw" / "sessions").mkdir()
            (vault / "raw" / "sessions" / "SESSION_TEMPLATE.md").write_text("template\n", encoding="utf-8")
            source = vault / "raw" / "new.md"
            source.write_text("new source\n", encoding="utf-8")
            calls = []

            def model(_prompt, _model):
                calls.append(True)
                return '{"classification":"C","summary":"small note","evidence_quotes":["new source"]}'

            first = run_brain_intake(
                vault, state_path=Path(tmp) / "state.json", local_model="local-model",
                max_files=25, max_chars=12000, max_bytes=200000, include_legacy=False,
                call_model=model, generated_at="2026-07-16T02:00:00+00:00",
            )
            second = run_brain_intake(
                vault, state_path=Path(tmp) / "state.json", local_model="local-model",
                max_files=25, max_chars=12000, max_bytes=200000, include_legacy=False,
                call_model=model, generated_at="2026-07-16T03:00:00+00:00",
            )
            self.assertEqual(first["processed"], 1)
            self.assertEqual(second["status"], "NO_WORK")
            self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
