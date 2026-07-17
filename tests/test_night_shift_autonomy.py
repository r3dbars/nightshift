import dataclasses
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_autonomy import (
    BLOCKED_POLICY,
    DOCS_REPAIR_POLICY,
    E2E_STRENGTHENING_POLICY,
    EXPLICIT_TEST_MISSION_POLICY,
    ISSUE_FIX_POLICY,
    POLICIES,
    REPAIR_POLICY,
    SAFE_REFACTOR_POLICY,
    TEST_STRENGTHENING_POLICY,
    candidate_prompt_rules,
    candidate_score_allowed,
    classify_path,
    clean_baseline_allowed,
    patch_limits,
    patch_risk_reasons,
    policy_accepts_files,
    policy_for_candidate,
    select_approved_verification,
    test_failure_signature,
    verification_outcome,
)


class ChangePolicyTests(unittest.TestCase):
    def test_policies_are_frozen_and_have_the_required_limits(self):
        expected = {
            "repair": (False, ("source", "test"), 4, 300),
            "test-strengthening": (True, ("test",), 1, 120),
            "explicit-test-mission": (True, ("test",), 1, 120),
            "e2e-strengthening": (True, ("e2e",), 1, 160),
            "docs-repair": (True, ("docs",), 2, 120),
            "issue-fix": (True, ("source", "test"), 2, 180),
            "safe-refactor": (True, ("source",), 1, 120),
        }
        self.assertEqual(set(POLICIES), set(expected))
        for name, (clean, kinds, files, lines) in expected.items():
            with self.subTest(name=name):
                policy = POLICIES[name]
                self.assertEqual(
                    (policy.allow_clean_baseline, policy.allowed_file_kinds, policy.max_files, policy.max_changed_lines),
                    (clean, kinds, files, lines),
                )
                self.assertEqual(policy.minimum_score, "MAYBE")
                self.assertTrue(policy.prompt_rules)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            REPAIR_POLICY.max_files = 99
        with self.assertRaises(TypeError):
            POLICIES["other"] = REPAIR_POLICY

    def test_policy_selection_preserves_every_explicit_intent(self):
        expected = {
            "repair": REPAIR_POLICY,
            "test-strengthening": TEST_STRENGTHENING_POLICY,
            "explicit-test-mission": EXPLICIT_TEST_MISSION_POLICY,
            "e2e-strengthening": E2E_STRENGTHENING_POLICY,
            "docs-repair": DOCS_REPAIR_POLICY,
            "issue-fix": ISSUE_FIX_POLICY,
            "safe-refactor": SAFE_REFACTOR_POLICY,
        }
        for intent, policy in expected.items():
            with self.subTest(intent=intent):
                self.assertIs(policy_for_candidate({"draft_intent": intent}), policy)
        self.assertIs(policy_for_candidate({"intent": "SAFE_REFACTOR"}), BLOCKED_POLICY)

    def test_unknown_or_missing_intent_is_not_executable(self):
        self.assertIs(policy_for_candidate({}), BLOCKED_POLICY)
        self.assertIs(policy_for_candidate({"draft_intent": "new-unreviewed-kind"}), BLOCKED_POLICY)
        self.assertFalse(policy_accepts_files(BLOCKED_POLICY, ["src/app.py"]))
        self.assertEqual(patch_limits({}), (0, 0))

    def test_existing_explicit_mission_shape_keeps_clean_baseline_behavior(self):
        candidate = {
            "kind": "mission",
            "proof_kind": "test",
            "semantic_contract": {"minimum_target_invocations": 1},
        }
        self.assertIs(policy_for_candidate(candidate), EXPLICIT_TEST_MISSION_POLICY)
        self.assertTrue(clean_baseline_allowed(candidate))

    def test_clean_baseline_and_limits_are_direct_policy_lookups(self):
        self.assertFalse(clean_baseline_allowed({"draft_intent": "repair"}))
        for intent in (
            "test-strengthening",
            "explicit-test-mission",
            "e2e-strengthening",
            "docs-repair",
            "issue-fix",
            "safe-refactor",
        ):
            with self.subTest(intent=intent):
                self.assertTrue(clean_baseline_allowed({"draft_intent": intent}))
        self.assertEqual(patch_limits({"draft_intent": "docs-repair"}), (2, 120))
        self.assertEqual(patch_limits({"draft_intent": "e2e-strengthening"}), (1, 160))
        self.assertEqual(patch_limits({"draft_intent": "test-strengthening"}), (1, 120))
        self.assertEqual(patch_limits({"draft_intent": "issue-fix"}), (2, 180))
        self.assertEqual(patch_limits({"draft_intent": "safe-refactor"}), (1, 120))
        self.assertEqual(patch_limits({"draft_intent": "repair"}), (4, 300))

    def test_prompt_rules_match_selected_policy_and_state_key_boundaries(self):
        self.assertEqual(
            candidate_prompt_rules({"draft_intent": "docs-repair"}),
            DOCS_REPAIR_POLICY.prompt_rules,
        )
        self.assertIn("failing baseline", candidate_prompt_rules({"draft_intent": "repair"}))
        self.assertIn("one approved source file", candidate_prompt_rules({"draft_intent": "safe-refactor"}))

    def test_score_gate_uses_existing_keep_maybe_reject_order(self):
        for intent in POLICIES:
            with self.subTest(intent=intent):
                base = {"draft_intent": intent}
                self.assertTrue(candidate_score_allowed({**base, "score": "KEEP"}))
                self.assertTrue(candidate_score_allowed({**base, "score": "maybe"}))
                self.assertFalse(candidate_score_allowed({**base, "score": "REJECT"}))
                self.assertFalse(candidate_score_allowed(base))
                self.assertFalse(candidate_score_allowed({**base, "score": 100}))


class PathPolicyTests(unittest.TestCase):
    def test_classify_path_covers_each_kind(self):
        cases = {
            "README.md": "docs",
            "docs/guide.rst": "docs",
            "tests/e2e/login.spec.ts": "e2e",
            "cypress/e2e/login.cy.ts": "e2e",
            "tests/test_policy.py": "test",
            "lib/value.test.ts": "test",
            "Sources/AppTests.swift": "test",
            "src/app.py": "source",
            "bin/night-shift": "source",
            "app/page.tsx": "source",
            "src/contest.py": "source",
            ".github/workflows/test.yml": "forbidden",
            "AGENTS.md": "forbidden",
            "SAFETY.md": "forbidden",
            "docs/SAFETY.md": "forbidden",
            "package.json": "forbidden",
            "scripts/release.sh": "forbidden",
            "scripts/deploy-production.py": "forbidden",
            "src/generated/client.ts": "forbidden",
            "assets/logo.png": "forbidden",
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(classify_path(path), expected)

    def test_classify_path_rejects_unsafe_or_non_file_paths(self):
        for path in ("", " src/app.py", "src/app.py ", "/src/app.py", "~/app.py", "src\\app.py", "src/../app.py", "src//app.py", "src/"):
            with self.subTest(path=path):
                self.assertEqual(classify_path(path), "forbidden")

    def test_nested_e2e_takes_precedence_over_general_test_classification(self):
        self.assertEqual(classify_path("tests/e2e/test_checkout.py"), "e2e")

    def test_each_policy_accepts_only_its_allowed_file_kinds(self):
        self.assertTrue(policy_accepts_files(DOCS_REPAIR_POLICY, ["README.md", "docs/guide.md"]))
        self.assertFalse(policy_accepts_files(DOCS_REPAIR_POLICY, ["docs/guide.md", "src/app.py"]))
        self.assertTrue(policy_accepts_files(E2E_STRENGTHENING_POLICY, ["tests/e2e/login.spec.ts"]))
        self.assertFalse(policy_accepts_files(E2E_STRENGTHENING_POLICY, ["tests/unit/login.test.ts"]))
        self.assertTrue(policy_accepts_files(TEST_STRENGTHENING_POLICY, ["tests/test_app.py"]))
        self.assertFalse(policy_accepts_files(TEST_STRENGTHENING_POLICY, ["src/app.py"]))
        self.assertTrue(policy_accepts_files(SAFE_REFACTOR_POLICY, ["src/app.py"]))
        self.assertFalse(policy_accepts_files(SAFE_REFACTOR_POLICY, ["tests/test_app.py"]))
        self.assertTrue(policy_accepts_files(ISSUE_FIX_POLICY, ["src/app.py", "tests/test_app.py"]))

    def test_file_gate_enforces_nonempty_unique_and_maximum_file_sets(self):
        self.assertFalse(policy_accepts_files(REPAIR_POLICY, []))
        self.assertFalse(policy_accepts_files(REPAIR_POLICY, ["src/app.py", "src/app.py"]))
        self.assertTrue(
            policy_accepts_files(
                REPAIR_POLICY,
                ["src/a.py", "src/b.py", "tests/test_a.py", "tests/test_b.py"],
            )
        )
        self.assertFalse(
            policy_accepts_files(
                REPAIR_POLICY,
                ["src/a.py", "src/b.py", "src/c.py", "src/d.py", "src/e.py"],
            )
        )
        self.assertFalse(policy_accepts_files(ISSUE_FIX_POLICY, ["src/a.py", "src/b.py", "tests/test_a.py"]))
        self.assertFalse(policy_accepts_files(REPAIR_POLICY, ["package.json"]))
        self.assertFalse(policy_accepts_files(REPAIR_POLICY, None))
        self.assertFalse(policy_accepts_files(REPAIR_POLICY, [["src/app.py"]]))


class VerificationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.approved = (
            ("python3", "-m", "unittest"),
            ("python3", "-m", "unittest", "tests.test_app"),
            ("pytest", "-k", "focused case"),
        )

    def test_exact_approved_candidate_command_is_selected(self):
        selected = select_approved_verification(
            {"verification": "python3 -m unittest tests.test_app"},
            self.approved,
        )
        self.assertEqual(selected, self.approved[1])

    def test_structured_candidate_argv_must_match_exactly(self):
        self.assertEqual(
            select_approved_verification(
                {"verification_argv": ["python3", "-m", "unittest", "tests.test_app"]},
                self.approved,
            ),
            self.approved[1],
        )
        self.assertEqual(
            select_approved_verification({"verification_argv": ["pytest"]}, self.approved),
            (),
        )

    def test_quoted_arguments_are_parsed_as_argv(self):
        selected = select_approved_verification(
            {"verification": 'pytest -k "focused case"'},
            self.approved,
        )
        self.assertEqual(selected, self.approved[2])

    def test_unapproved_or_malformed_command_fails_closed(self):
        for verification in (None, "", "pytest", 'pytest -k "unterminated'):
            with self.subTest(verification=verification):
                self.assertEqual(
                    select_approved_verification({"verification": verification}, self.approved),
                    (),
                )

    def test_shell_metacharacters_always_fail_closed(self):
        dangerous = (
            "python3 -m unittest; rm -rf tmp",
            "python3 -m unittest && echo done",
            "python3 -m unittest | tee out",
            "python3 -m unittest > out",
            "python3 -m unittest $(whoami)",
            "python3 -m unittest `whoami`",
            "python3 -m unittest\nrm tmp",
            "python3 -m unittest *",
            "python3 -m unittest # skip",
        )
        for verification in dangerous:
            with self.subTest(verification=verification):
                self.assertEqual(
                    select_approved_verification({"verification": verification}, self.approved),
                    (),
                )

    def test_string_approved_commands_are_supported_and_empty_set_returns_empty(self):
        self.assertEqual(
            select_approved_verification(
                {"verification": "python3 -m unittest tests.test_app"},
                ["python3 -m unittest", "python3 -m unittest tests.test_app"],
            ),
            ("python3", "-m", "unittest", "tests.test_app"),
        )
        self.assertEqual(select_approved_verification({"verification": "pytest"}, ()), ())

    def test_verification_outcome_requires_a_real_test_failure_signature(self):
        self.assertEqual(verification_outcome(0, "all good"), "PASS")
        self.assertEqual(verification_outcome(1, "FAILED tests/test_app.py::test_login"), "FAILING")
        self.assertEqual(verification_outcome(1, "FAILED (failures=2)"), "FAILING")
        self.assertEqual(verification_outcome(1, "wrapper exited unexpectedly"), "BLOCKED")
        self.assertEqual(verification_outcome(127, "command not found"), "BLOCKED")

    def test_failure_signature_distinguishes_different_failing_tests(self):
        first = "FAILED tests/test_app.py::test_login - AssertionError: expected 200 got 500"
        same = "FAILED tests/test_app.py::test_login - AssertionError: expected 200 got 500"
        other = "FAILED tests/test_app.py::test_logout - AssertionError: expected 204 got 500"
        self.assertEqual(test_failure_signature(first), test_failure_signature(same))
        self.assertNotEqual(test_failure_signature(first), test_failure_signature(other))
        self.assertEqual(test_failure_signature("1 test failed"), "")

    def test_source_patch_rejects_new_privileged_behavior(self):
        candidate = {"draft_intent": "safe-refactor"}
        risky = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1 +1,2 @@
 return value
+subprocess.run(['curl', url])
"""
        self.assertIn("process", " ".join(patch_risk_reasons(candidate, risky)))
        network = risky.replace("subprocess.run(['curl', url])", "requests.get(url)")
        self.assertIn("network", " ".join(patch_risk_reasons(candidate, network)))
        self.assertEqual(patch_risk_reasons({"draft_intent": "docs-repair"}, network), ())

    def test_source_patch_rejects_release_cli_actions(self):
        patch = """diff --git a/scripts/helper.sh b/scripts/helper.sh
--- a/scripts/helper.sh
+++ b/scripts/helper.sh
@@ -1 +1,2 @@
 echo ready
+gh release create v1.2.3
"""
        reasons = patch_risk_reasons({"draft_intent": "safe-refactor"}, patch)
        self.assertIn("release", " ".join(reasons))


if __name__ == "__main__":
    unittest.main()
