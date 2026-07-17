import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_host_git import (
    checkout_safety_reasons,
    publication_ci_reasons,
    safe_git_env,
)


def result(rc=0, stdout="", stderr=""):
    return SimpleNamespace(rc=rc, stdout=stdout, stderr=stderr)


class HostGitSafetyTests(unittest.TestCase):
    def test_safe_environment_disables_hooks_and_unsafe_protocols(self):
        env = safe_git_env({"PATH": "/usr/bin"})
        pairs = {
            env[f"GIT_CONFIG_KEY_{index}"]: env[f"GIT_CONFIG_VALUE_{index}"]
            for index in range(int(env["GIT_CONFIG_COUNT"]))
        }
        self.assertEqual(pairs["core.hooksPath"], "/dev/null")
        self.assertEqual(pairs["protocol.ext.allow"], "never")
        self.assertEqual(pairs["protocol.file.allow"], "never")
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")

    def test_checkout_rejects_executable_local_git_config(self):
        def fake(command, **_kwargs):
            if command[:3] == ["git", "config", "--local"]:
                return result(stdout="filter.evil.process /tmp/run-me\n")
            return result(stdout="src/app.py\n")

        reasons = checkout_safety_reasons(fake, Path("/repo"), "a" * 40)
        self.assertIn("executable driver", reasons[0])

    def test_checkout_rejects_filter_attributes(self):
        def fake(command, **_kwargs):
            if command[:3] == ["git", "config", "--local"]:
                return result(rc=1)
            if command[:3] == ["git", "ls-tree", "-r"]:
                return result(stdout=".gitattributes\nsrc/app.py\n")
            if command[:2] == ["git", "show"]:
                return result(stdout="*.py filter=evil\n")
            return result(rc=1)

        reasons = checkout_safety_reasons(fake, Path("/repo"), "b" * 40)
        self.assertIn("executable Git attribute", reasons[0])

    def test_publication_rejects_privileged_or_external_ci(self):
        def fake(command, **_kwargs):
            if command[:3] == ["git", "ls-tree", "-r"]:
                return result(stdout=".github/workflows/ci.yml\n.circleci/config.yml\n")
            if command[:2] == ["git", "show"]:
                return result(stdout="on:\n  pull_request_target:\n")
            return result(rc=1)

        reasons = publication_ci_reasons(fake, Path("/repo"), "c" * 40)
        self.assertTrue(any("external CI" in reason for reason in reasons))
        self.assertTrue(any("pull_request_target" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
