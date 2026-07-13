import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_setup import detected_tools, mode_counts, setup_has_changed, start_preview


MODE_DEFAULTS = {
    "quiet": {"local": 1, "windows": 1},
    "night-shift": {"local": 2, "windows": 2},
}


class SetupPolicyTests(unittest.TestCase):
    def test_tools_respect_health_and_privacy_route(self):
        rows = [
            ("local-models", "GREEN", "ready"),
            ("local-chat", "GREEN", "ready"),
            ("windows-worker", "GREEN", "ready"),
            ("gh-auth", "GREEN", "ready"),
        ]
        self.assertEqual(detected_tools(rows), ["local Mac AI", "GitHub CLI for repo context"])
        self.assertEqual(
            detected_tools(rows, "mac-and-lan"),
            ["local Mac AI", "another computer", "GitHub CLI for repo context"],
        )

    def test_mode_counts_describe_only_reachable_allowed_workers(self):
        rows = [
            ("local-models", "GREEN", "ready"),
            ("local-chat", "GREEN", "ready"),
            ("windows-worker", "GREEN", "ready"),
        ]
        self.assertEqual(mode_counts("quiet", MODE_DEFAULTS, rows), "unique task batches on this Mac")
        self.assertEqual(
            mode_counts("quiet", MODE_DEFAULTS, rows, "mac-and-lan"),
            "unique task batches on this Mac and the other computer",
        )
        unavailable = [(name, "YELLOW", message) for name, _, message in rows]
        self.assertEqual(
            mode_counts("quiet", MODE_DEFAULTS, unavailable),
            "planning brief only until worker AI is reachable",
        )

    def test_preview_states_real_boundaries(self):
        preview = start_preview(
            {
                "project": {"repo": "/repo"},
                "preferences": {
                    "mode": "quiet",
                    "permission": "draft-prs",
                    "execute_drafts": True,
                    "allow_draft_prs": True,
                    "stop": "8h",
                    "privacy_route": "mac-only",
                    "wake_goal": "draft-prs",
                },
            },
            [("windows-worker", "GREEN", "ready")],
            MODE_DEFAULTS,
        )
        self.assertIn("test-gated patches in disposable copies", preview)
        self.assertIn("May open test-passed draft PRs; never merges them", preview)
        self.assertIn("stop after 8 hours", preview)
        self.assertIn("Keep repo context on this Mac", preview)
        self.assertNotIn("Use: another computer", preview)
        self.assertIn("Never edits this checkout, merges, releases, deploys", preview)
        self.assertIn("Never deletes or reorganizes your files", preview)
        self.assertIn("changes billing, or changes repo visibility", preview)
        self.assertIn("night-shift doctor --repo /repo", preview)
        self.assertLessEqual(len(preview.splitlines()), 21)

    def test_timestamp_does_not_turn_repeat_setup_into_a_change(self):
        saved = {"schema_version": 4, "updated_at": "before", "preferences": {"mode": "quiet"}}
        proposed = {**saved, "updated_at": "after"}
        self.assertFalse(setup_has_changed(saved, proposed))
        proposed["preferences"] = {"mode": "night-shift"}
        self.assertTrue(setup_has_changed(saved, proposed))
        self.assertTrue(setup_has_changed({}, proposed))


if __name__ == "__main__":
    unittest.main()
