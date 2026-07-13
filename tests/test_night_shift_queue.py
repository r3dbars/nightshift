import json
import tempfile
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_queue import (
    QueueEvidenceIndex,
    RepoRevisionAdapter,
    TASK_LADDER,
    build_repo_work_queue,
    contains_identifier,
    goal_semantic_contract,
    is_test_path,
    python_owned_methods,
    symbol_is_test_addressable,
)
from night_shift_portfolio import PortfolioEngine
from night_shift_python_evidence import top_level_symbol_call_count_text
from night_shift_js_evidence import top_level_symbol_call_count_text as js_symbol_call_count_text


class QueueEvidenceTests(unittest.TestCase):
    def test_top_level_python_calls_count_direct_alias_and_module_forms(self):
        text = (
            "from pkg.tools import helper as renamed\n"
            "import pkg.tools as tools\n"
            "rebound = helper\n"
            "helper()\nrenamed()\ntools.helper()\npkg.tools.helper()\nrebound()\n"
        )
        self.assertEqual(top_level_symbol_call_count_text(text, "helper"), 5)
        self.assertIsNone(top_level_symbol_call_count_text("def broken(:", "helper"))

    def test_top_level_python_fixture_parameter_counts_as_usage(self):
        text = "def test_uses_fixture(helper):\n    assert helper\n"
        self.assertEqual(top_level_symbol_call_count_text(text, "helper"), 1)

    def test_typescript_invocation_gap_uses_complete_regex_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "metrics.ts").write_text(
                "export function formatPercent(value: number) { return `${value}%`; }\n",
                encoding="utf-8",
            )
            (repo / "metrics.test.mjs").write_text(
                "describe('metrics', () => {});\n", encoding="utf-8"
            )
            scan = {
                "tracked_files": ["metrics.ts", "metrics.test.ts"],
                "source_files": ["metrics.ts"],
                "test_files": ["metrics.test.mjs"],
                "coverage_test_files": ["metrics.test.mjs"],
            }
            gap = QueueEvidenceIndex(repo, scan).coverage_gaps(["metrics.ts"])[0]
            invocation = next(
                value for key, value in gap[2].items() if key.startswith("invocation-index/")
            )
            self.assertIn("analysis=typescript-regex", invocation)
            self.assertIn("scope=test-files-only", invocation)
            self.assertIn("call_matches=0", invocation)
            self.assertEqual(js_symbol_call_count_text("formatPercent(42)", "formatPercent"), 1)

    def test_top_level_python_gap_gets_complete_ast_invocation_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "tools.py").write_text(
                "def helper(value):\n    return value + 1\n", encoding="utf-8"
            )
            (repo / "test_tools.py").write_text(
                "def test_other():\n    assert True\n", encoding="utf-8"
            )
            scan = {
                "tracked_files": ["tools.py", "test_tools.py"],
                "source_files": ["tools.py"],
                "test_files": ["test_tools.py"],
                "coverage_test_files": ["test_tools.py"],
            }
            gap = QueueEvidenceIndex(repo, scan).coverage_gaps(["tools.py"])[0]
            invocation = next(
                value for key, value in gap[2].items() if key.startswith("invocation-index/")
            )
            self.assertIn("owner=none", invocation)
            self.assertIn("analysis=python-ast", invocation)
            self.assertIn("call_matches=0", invocation)

    def test_top_level_python_incomplete_ast_scan_is_not_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "tools.py").write_text(
                "def helper(value):\n    return value + 1\n", encoding="utf-8"
            )
            (repo / "test_tools.py").write_text("def broken(:\n", encoding="utf-8")
            scan = {
                "recent_files": ["tools.py"],
                "tracked_files": ["tools.py", "test_tools.py"],
                "source_files": ["tools.py"],
                "test_files": ["test_tools.py"],
                "coverage_test_files": ["test_tools.py"],
                "test_commands": ["python -m unittest"],
            }
            queue = build_repo_work_queue(
                repo, scan, "night-shift", "draft-local",
                run_cmd=lambda *args, **kwargs: SimpleNamespace(rc=1, stdout="", stderr=""),
                detect_test_commands=lambda *args, **kwargs: [],
            )
            task = next(item for item in queue if item["slug"].startswith("changed-file-proof-"))
            evidence = "\n".join(task["evidence_sources"].values())
            self.assertIn("scan_complete=false", evidence)
            self.assertFalse(task["executable"])

    def test_js_ts_addressability_excludes_private_top_level_helpers(self):
        source = (
            "function startOfDay(date: Date) { return date; }\n"
            "export function loadAnalytics() { return startOfDay(new Date()); }\n"
            "export class Engine {\n  run() { return true; }\n  private stop() {}\n}\n"
        )
        self.assertFalse(symbol_is_test_addressable("analytics.ts", source, "startOfDay"))
        self.assertTrue(symbol_is_test_addressable("analytics.ts", source, "loadAnalytics"))
        self.assertTrue(symbol_is_test_addressable("analytics.ts", source, "Engine"))
        self.assertFalse(symbol_is_test_addressable("analytics.ts", source, "run"))
        self.assertFalse(symbol_is_test_addressable("analytics.ts", source, "stop"))
        self.assertFalse(symbol_is_test_addressable(
            "analytics.ts", "function privateHelper() {}\nif (ready) {\n  privateHelper();\n}\n", "privateHelper"
        ))

    def test_coverage_gaps_skip_test_files_and_private_ts_helpers(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "analytics.ts").write_text(
                "function privateHelper() { return 1; }\nexport function publicApi() { return privateHelper(); }\n",
                encoding="utf-8",
            )
            (repo / "analytics.test.ts").write_text(
                "export function testHelper() { return true; }\n", encoding="utf-8"
            )
            scan = {
                "tracked_files": ["analytics.ts", "analytics.test.ts"],
                "source_files": ["analytics.ts", "analytics.test.ts"],
                "test_files": ["analytics.test.ts"],
                "coverage_test_files": ["analytics.test.ts"],
            }
            gaps = QueueEvidenceIndex(repo, scan).coverage_gaps(
                ["analytics.test.ts", "analytics.ts"]
            )
            self.assertEqual(
                [(path, symbol) for path, symbol, _ in gaps],
                [("analytics.ts", "publicApi")],
            )
    def test_python_owned_methods_ignore_top_level_and_private_functions(self):
        self.assertEqual(
            python_owned_methods(
                "def top(): pass\nclass Engine:\n"
                "    def run(self): pass\n"
                "    @staticmethod\n    def stop(): pass\n"
                "    @property\n    def valid(self): return True\n"
                "    @valid.setter\n    def valid(self, value): pass\n"
                "    @functools.cached_property\n    def cached(self): return True\n"
                "    def _private(self): pass\n"
            ),
            [("Engine", "run"), ("Engine", "stop")],
        )
        source = "class PatchCheck:\n    @property\n    def valid(self): return True\n"
        self.assertFalse(symbol_is_test_addressable("protocol.py", source, "valid"))
        duplicate = source + "class Other:\n    def valid(self): return True\n"
        self.assertTrue(symbol_is_test_addressable("protocol.py", duplicate, "valid"))
        top_level = source + "def valid(): return True\n"
        self.assertTrue(symbol_is_test_addressable("protocol.py", top_level, "valid"))
        aliased = (
            "from functools import cached_property as cached\n"
            "class Engine:\n    @cached\n    def value(self): return 1\n"
        )
        self.assertFalse(symbol_is_test_addressable("engine.py", aliased, "value"))

    def test_goal_semantic_contract_preserves_explicit_outcome_and_order_requirements(self):
        contract = goal_semantic_contract(
            "Add a test proving ordered remove and prune calls and both boolean return outcomes"
        )
        self.assertEqual(contract["minimum_target_invocations"], 2)
        self.assertEqual(contract["required_boolean_outcomes"], [True, False])
        self.assertEqual(contract["ordered_terms"], ["remove", "prune"])
        self.assertEqual(
            goal_semantic_contract("Add a focused behavioral test for cleanup"),
            {"minimum_target_invocations": 1},
        )
        self.assertNotIn(
            "required_boolean_outcomes",
            goal_semantic_contract("Test the truthful and falsehood labels"),
        )

    def test_issue_symbols_rank_exact_source_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src" / "primary.py").write_text("def repair_session():\n    pass\n", encoding="utf-8")
            (repo / "src" / "secondary.py").write_text("def other():\n    pass\n", encoding="utf-8")
            index = QueueEvidenceIndex(repo, {
                "tracked_files": ["src/primary.py", "src/secondary.py"],
                "source_files": ["src/primary.py", "src/secondary.py"],
            })
            files, matches = index.issue_candidate_files({
                "title": "Repair `repair_session()`",
                "body": "The failure is in src/secondary.py but `repair_session` is the exact symbol.",
            })
            self.assertEqual(files, ["src/primary.py", "src/secondary.py"])
            self.assertEqual(matches, 2)

    def test_coverage_evidence_is_complete_only_when_every_test_is_indexed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src.py").write_text("def public_api():\n    return 1\n", encoding="utf-8")
            (repo / "test_src.py").write_text("def test_other():\n    pass\n", encoding="utf-8")
            scan = {
                "tracked_files": ["src.py", "test_src.py"],
                "source_files": ["src.py"],
                "test_files": ["test_src.py"],
                "coverage_test_files": ["test_src.py"],
            }
            gaps = QueueEvidenceIndex(repo, scan).coverage_gaps(["src.py"])
            self.assertEqual(gaps[0][0:2], ("src.py", "public_api"))
            evidence = next(iter(gaps[0][2].values()))
            self.assertIn("identifier_matches=0", evidence)
            self.assertIn("scan_complete=true", evidence)
            scan["coverage_test_files"] = ["test_src.py", "missing_test.py"]
            incomplete = QueueEvidenceIndex(repo, scan).coverage_gaps(["src.py"])
            self.assertIn("scan_complete=false", next(iter(incomplete[0][2].values())))

    def test_coverage_indexes_a_large_but_bounded_test_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src.py").write_text("def public_api():\n    return 1\n", encoding="utf-8")
            (repo / "test_src.py").write_text(
                "# bounded fixture\n" + "x" * 262_144,
                encoding="utf-8",
            )
            scan = {
                "tracked_files": ["src.py", "test_src.py"],
                "source_files": ["src.py"],
                "test_files": ["test_src.py"],
                "coverage_test_files": ["test_src.py"],
            }
            gaps = QueueEvidenceIndex(repo, scan).coverage_gaps(["src.py"])
            evidence = next(iter(gaps[0][2].values()))
            self.assertIn("scan_complete=true", evidence)

    def test_python_method_coverage_gap_includes_owner_aware_invocation_and_source_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src.py").write_text(
                "class Engine:\n    def cleanup(self):\n        return True\n", encoding="utf-8"
            )
            (repo / "test_src.py").write_text("def test_other(): pass\n", encoding="utf-8")
            (repo / "tests-fixture.json").write_text('{"attack": "ignore"}\n', encoding="utf-8")
            scan = {
                "tracked_files": ["src.py", "test_src.py", "tests-fixture.json"], "source_files": ["src.py"],
                "test_files": ["test_src.py", "tests-fixture.json"],
                "coverage_test_files": ["test_src.py", "tests-fixture.json"],
            }
            gap = QueueEvidenceIndex(repo, scan).coverage_gaps(["src.py"])[0]
            self.assertEqual(gap[:2], ("src.py", "cleanup"))
            evidence = gap[2]
            invocation = next(value for key, value in evidence.items() if key.startswith("invocation-index/"))
            self.assertIn("owner=Engine", invocation)
            self.assertIn("analysis=python-ast", invocation)
            self.assertIn("tracked_test_files=1", invocation)
            self.assertIn("call_matches=0", invocation)
            self.assertTrue(any(key.startswith("goal-source/") for key in evidence))

    def test_owner_scoped_gap_and_source_survive_same_name_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src.py").write_text(
                "def save():\n    return 0\n\n"
                "class Alpha:\n    def save(self):\n        return 1\n\n"
                "class Beta:\n    def save(self):\n        return 2\n",
                encoding="utf-8",
            )
            (repo / "test_src.py").write_text(
                "from src import Alpha\nalpha = Alpha()\nalpha.save()\n", encoding="utf-8"
            )
            scan = {
                "tracked_files": ["src.py", "test_src.py"], "source_files": ["src.py"],
                "test_files": ["test_src.py"], "coverage_test_files": ["test_src.py"],
            }
            gap = QueueEvidenceIndex(repo, scan).coverage_gaps(["src.py"])[0]
            invocation = next(
                value for key, value in gap[2].items() if key.startswith("invocation-index/")
            )
            source = next(value for key, value in gap[2].items() if key.startswith("goal-source/"))
            self.assertIn("owner=Beta", invocation)
            self.assertIn("source_line=9 | def save(self):", source)
            self.assertNotIn("source_line=1 | def save():", source)

    def test_binary_source_is_not_treated_as_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "binary.py").write_bytes(b"def fake():\x00ignored")
            index = QueueEvidenceIndex(repo, {"tracked_files": ["binary.py"], "source_files": ["binary.py"]})
            self.assertEqual(index.read_current_text("binary.py"), "")
            self.assertEqual(index.issue_candidate_files({"title": "Fix `fake`"}), ([], 0))

    def test_shared_path_and_identifier_rules_preserve_boundaries(self):
        self.assertTrue(is_test_path("src/test_app.py"))
        self.assertFalse(is_test_path("src/contest_app.py"))
        self.assertTrue(contains_identifier("run()", "run"))
        self.assertFalse(contains_identifier("runtime = 1", "run"))

    def test_malicious_refs_branches_and_paths_never_reach_git(self):
        calls = []

        def runner(argv, **kwargs):
            calls.append((argv, kwargs))
            return SimpleNamespace(rc=1, stdout="", stderr="")

        adapter = RepoRevisionAdapter(Path("/repo"), runner)
        self.assertFalse(adapter.ensure_pr_ref("1;touch /tmp/pwn", "a" * 40))
        self.assertFalse(adapter.ensure_pr_ref("1", "HEAD"))
        self.assertFalse(adapter.ensure_branch_ref("--upload-pack=evil", "a" * 40))
        self.assertFalse(adapter.ensure_branch_ref("feature/../main", "a" * 40))
        self.assertFalse(adapter.file_exists("../secret", "a" * 40))
        self.assertFalse(adapter.file_exists(".git/config", "a" * 40))
        self.assertEqual(
            [argv for argv, _ in calls],
            [
                ["git", "cat-file", "-e", f"{'a' * 40}^{{commit}}"],
                ["git", "cat-file", "-e", f"{'a' * 40}^{{commit}}"],
                ["git", "cat-file", "-e", f"{'a' * 40}^{{commit}}"],
            ],
        )
        self.assertFalse(any("fetch" in argv for argv, _ in calls))

    def test_fetch_uses_literal_allowlisted_refs_and_rechecks_commit(self):
        calls = []
        availability = iter([1, 0])

        def runner(argv, **kwargs):
            calls.append((argv, kwargs))
            if argv[1:3] == ["cat-file", "-e"]:
                return SimpleNamespace(rc=next(availability), stdout="", stderr="")
            return SimpleNamespace(rc=0, stdout="", stderr="")

        ref = "b" * 40
        adapter = RepoRevisionAdapter(Path("/repo"), runner)
        self.assertTrue(adapter.ensure_pr_ref("42", ref))
        self.assertEqual(calls[1][0], ["git", "fetch", "--quiet", "--no-tags", "origin", "refs/pull/42/head"])
        self.assertEqual(calls[1][1]["timeout"], 120)

    def test_log_paths_are_deduped_suffixes_and_list_files_requires_sha(self):
        adapter = RepoRevisionAdapter(Path("/repo"), lambda *_args, **_kwargs: None)
        self.assertEqual(
            adapter.log_paths("error /workspace/src/app.py:4\nagain src/app.py"),
            ["workspace/src/app.py", "src/app.py", "app.py"],
        )
        self.assertIsNone(adapter.list_files("HEAD"))


class BuildRepoWorkQueueTests(unittest.TestCase):
    def _run_cmd(self, argv, cwd=None, timeout=60, env=None, pid_log=None):
        return SimpleNamespace(rc=1, stdout="", stderr="")

    def _detect_test_commands(self, repo, tracked, source_ref=""):
        return []

    def test_quiet_mode_limits_queue_to_ten_and_ranks_by_ladder(self):
        scan = {
            "recent_files": ["src/app.py"],
            "source_files": ["src/app.py"],
            "test_files": ["test_app.py"],
            "doc_files": ["README.md"],
            "todo_sample": ["src/app.py:3: TODO fix this"],
            "test_commands": ["python -m pytest"],
            "tracked_files": ["src/app.py", "test_app.py", "README.md"],
        }
        queue = build_repo_work_queue(
            None, scan, "quiet", "brief",
            run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
        )
        self.assertLessEqual(len(queue), 10)
        priorities = [item["selection_priority"] for item in queue]
        self.assertEqual(priorities, sorted(priorities, reverse=True))
        for item in queue:
            self.assertIn(item["ladder"], TASK_LADDER)
            self.assertEqual(item["ladder_priority"], TASK_LADDER[item["ladder"]])

    def test_slugs_are_deduped_and_insertion_order_preserved_within_ties(self):
        scan = {
            "recent_files": [],
            "source_files": [f"src/f{i}.py" for i in range(6)],
            "test_files": [],
            "doc_files": [],
            "todo_sample": [],
            "test_commands": [],
            "tracked_files": [f"src/f{i}.py" for i in range(6)],
        }
        queue = build_repo_work_queue(
            None, scan, "night-shift", "brief",
            run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
        )
        slugs = [item["slug"] for item in queue]
        self.assertEqual(len(slugs), len(set(slugs)))
        source_map_items = [item for item in queue if item["slug"].startswith("source-map-")]
        self.assertEqual([item["slug"] for item in source_map_items], sorted(item["slug"] for item in source_map_items))

    def test_goal_guidance_inserts_mission_brief_first_by_priority(self):
        scan = {
            "recent_files": ["src/app.py"],
            "source_files": ["src/app.py"],
            "test_files": [],
            "doc_files": [],
            "todo_sample": [],
            "test_commands": [],
            "tracked_files": ["src/app.py"],
        }
        queue = build_repo_work_queue(
            None, scan, "quiet", "brief", guidance="goal", goal_text="Fix the login bug",
            run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
        )
        self.assertEqual(queue[0]["slug"], "mission-brief")
        self.assertEqual(queue[0]["ladder"], "repair")

    def test_goal_guidance_grounding_finds_named_symbol_outside_recent_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "recent.py").write_text("def unrelated():\n    return 1\n", encoding="utf-8")
            (repo / "drafts.py").write_text(
                "class DraftEngine:\n    def cleanup(self):\n        return True\n", encoding="utf-8"
            )
            (repo / "test_drafts.py").write_text("def test_other():\n    pass\n", encoding="utf-8")
            scan = {
                "recent_files": ["recent.py"],
                "source_files": ["recent.py", "drafts.py"],
                "test_files": ["test_drafts.py"],
                "doc_files": [], "todo_sample": [],
                "test_commands": ["python -m unittest"],
                "tracked_files": ["recent.py", "drafts.py", "test_drafts.py"],
            }
            queue = build_repo_work_queue(
                repo, scan, "afterburner", "draft-local", guidance="goal",
                goal_text="Add a behavioral test for DraftEngine.cleanup return value",
                run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
            )
            mission = next(item for item in queue if item["slug"] == "mission-brief")
            self.assertIn("drafts.py", mission["files"])
            self.assertIn("test_drafts.py", mission["files"])
            source_evidence = "\n".join(
                value for key, value in mission["evidence_sources"].items()
                if key.startswith("goal-source/")
            )
            self.assertIn("source_file=drafts.py", source_evidence)
            evidence = "\n".join(mission["evidence_sources"].values())
            self.assertIn("symbol=cleanup", evidence)
            self.assertIn("symbol=cleanup call_matches=0", evidence)
            self.assertIn("owner=DraftEngine", evidence)
            self.assertIn("analysis=python-ast", evidence)
            self.assertIn("def cleanup(self):", evidence)
            self.assertIn("return True", evidence)
            self.assertTrue(mission["executable"])
            self.assertIn("ACTION_TYPE: draft-pr-candidate", mission["prompt"])
            self.assertEqual(mission["semantic_contract"], {"minimum_target_invocations": 1})
            self.assertEqual(
                mission["signal"], "Add a behavioral test for DraftEngine.cleanup return value"
            )

            changed = build_repo_work_queue(
                repo, scan, "afterburner", "draft-local", guidance="goal",
                goal_text="Add a behavioral test for DraftEngine.cleanup failure path",
                run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
            )
            changed_mission = next(item for item in changed if item["slug"] == "mission-brief")
            self.assertNotEqual(mission["signal"], changed_mission["signal"])
            self.assertNotEqual(
                PortfolioEngine.task_fingerprint("owner/repo", "a" * 40, mission),
                PortfolioEngine.task_fingerprint("owner/repo", "a" * 40, changed_mission),
            )

    def test_typescript_gap_uses_full_coverage_test_set_and_is_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "analytics.ts").write_text(
                "export function formatPercent(value: number) { return `${Math.round(value)}%`; }\n",
                encoding="utf-8",
            )
            (repo / "tests" / "unit" / "lib").mkdir(parents=True)
            (repo / "tests" / "unit" / "lib" / "analytics-metrics.test.ts").write_text(
                "describe('metrics', () => {});\n", encoding="utf-8"
            )
            scan = {
                "recent_files": ["analytics.ts"],
                "source_files": ["analytics.ts"],
                "test_files": [],
                "coverage_test_files": ["tests/unit/lib/analytics-metrics.test.ts"],
                "test_commands": ["npm run test:unit:vitest"],
                "tracked_files": ["analytics.ts", "tests/unit/lib/analytics-metrics.test.ts"],
            }
            queue = build_repo_work_queue(
                repo, scan, "afterburner", "draft-local",
                run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
            )
            task = next(item for item in queue if item["slug"].startswith("changed-file-proof-"))
            self.assertTrue(task["executable"])
            self.assertIn("tests/unit/lib/analytics-metrics.test.ts", task["files"])
            self.assertIn("analysis=typescript-regex", "\n".join(task["evidence_sources"].values()))

    def test_invocation_gap_is_owner_aware_and_understands_import_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "drafts.py").write_text(
                "class DraftEngine:\n    def cleanup(self):\n        return True\n", encoding="utf-8"
            )
            (repo / "test_drafts.py").write_text(
                "from drafts import DraftEngine as DE\n"
                "class Other:\n    def cleanup(self): pass\n"
                "Other().cleanup()\n"
                "engine = DE()\n"
                "engine.cleanup()\n",
                encoding="utf-8",
            )
            index = QueueEvidenceIndex(repo, {
                "tracked_files": ["drafts.py", "test_drafts.py"],
                "source_files": ["drafts.py"], "test_files": ["test_drafts.py"],
                "coverage_test_files": ["test_drafts.py"],
            })
            evidence = "\n".join(index.invocation_gap("drafts.py", "cleanup", "DraftEngine").values())
            self.assertIn("symbol=cleanup call_matches=1", evidence)

    def test_incomplete_invocation_index_blocks_model_readiness(self):
        task = {
            "slug": "mission-brief", "kind": "mission", "files": ["src.py"],
            "verification_commands": ["python -m unittest"],
            "evidence_sources": {
                "invocation-index/src-cleanup.txt": "scan_complete=false",
                "coverage-index/other.txt": "scan_complete=true\nidentifier_matches=0",
            },
        }
        from night_shift_selection import model_task_readiness_reasons
        self.assertIn(
            "named-symbol invocation index is incomplete",
            model_task_readiness_reasons(task, "afterburner", "test cleanup"),
        )

    def test_empty_test_corpus_never_claims_complete_invocation_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "drafts.py").write_text(
                "class DraftEngine:\n    def cleanup(self): return True\n", encoding="utf-8"
            )
            index = QueueEvidenceIndex(repo, {
                "tracked_files": ["drafts.py"], "source_files": ["drafts.py"],
                "test_files": [], "coverage_test_files": [],
            })
            evidence = "\n".join(index.invocation_gap("drafts.py", "cleanup", "DraftEngine").values())
            self.assertIn("tracked_test_files=0", evidence)
            self.assertIn("scan_complete=false", evidence)

    def test_non_dotted_goal_never_enables_ast_backed_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app.py").write_text("def cleanup():\n    return True\n", encoding="utf-8")
            (repo / "test_app.py").write_text("def test_other():\n    pass\n", encoding="utf-8")
            scan = {
                "recent_files": ["app.py"], "source_files": ["app.py"],
                "test_files": ["test_app.py"], "coverage_test_files": ["test_app.py"],
                "tracked_files": ["app.py", "test_app.py"], "doc_files": [],
                "todo_sample": [], "test_commands": ["python -m unittest"],
            }
            queue = build_repo_work_queue(
                repo, scan, "afterburner", "draft-local", guidance="goal",
                goal_text="Add a cleanup behavioral test",
                run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
            )
            mission = next(item for item in queue if item["slug"] == "mission-brief")
            self.assertFalse(mission["executable"])

    def test_typescript_side_effect_gap_stays_analysis_only_for_draft_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "analytics.ts").write_text(
                "export async function loadAnalytics(id: string) {\n"
                "  return withUserContext(id, async () => []);\n"
                "}\n",
                encoding="utf-8",
            )
            (repo / "analytics.test.ts").write_text(
                "describe('analytics', () => {});\n", encoding="utf-8"
            )
            scan = {
                "recent_files": ["analytics.ts"],
                "source_files": ["analytics.ts"],
                "test_files": ["analytics.test.ts"],
                "coverage_test_files": ["analytics.test.ts"],
                "tracked_files": ["analytics.ts", "analytics.test.ts"],
                "test_commands": ["npm run test:unit"],
                "doc_files": [], "todo_sample": [],
            }
            queue = build_repo_work_queue(
                repo, scan, "quiet", "draft-local",
                run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
            )
            gap = next(item for item in queue if item["slug"].startswith("changed-file-proof-"))
            self.assertFalse(gap["executable"])

            from night_shift_selection import model_ready_tasks
            ready, skipped = model_ready_tasks(queue, "quiet", permission="draft-local")
            self.assertNotIn(gap, ready)
            self.assertTrue(any(row["slug"] == gap["slug"] for row in skipped))
            self.assertIn("no safe automatic patch path", next(
                row["reason"] for row in skipped if row["slug"] == gap["slug"]
            ))

    def test_failed_ci_uses_injected_run_cmd_and_detect_test_commands(self):
        calls = []

        def run_cmd(argv, cwd=None, timeout=60, env=None, pid_log=None):
            calls.append(argv)
            if argv[:3] == ["git", "cat-file", "-e"]:
                return SimpleNamespace(rc=0, stdout="", stderr="")
            if argv[:3] == ["git", "ls-tree", "-r"]:
                return SimpleNamespace(rc=0, stdout="src/app.py\n", stderr="")
            return SimpleNamespace(rc=0, stdout="", stderr="")

        detect_calls = []

        def detect_test_commands(repo, tracked, source_ref=""):
            detect_calls.append((repo, tracked, source_ref))
            return ["custom test command"]

        source_ref = "a" * 40
        scan = {
            "recent_files": [],
            "source_files": [],
            "test_files": [],
            "doc_files": [],
            "todo_sample": [],
            "test_commands": ["fallback test"],
            "tracked_files": [],
            "github_failed_runs_raw": json.dumps([
                {"databaseId": 42, "headSha": source_ref, "headBranch": "fix-branch", "updatedAt": "2026-01-01T00:00:00Z"}
            ]),
            "github_failed_logs_raw": json.dumps([
                {"run": {"databaseId": 42}, "log": "AssertionError in src/app.py"}
            ]),
        }
        queue = build_repo_work_queue(
            Path("/repo"), scan, "quiet", "brief",
            run_cmd=run_cmd, detect_test_commands=detect_test_commands,
        )
        failed_ci = next(item for item in queue if item["slug"] == "failed-ci-42")
        self.assertEqual(failed_ci["verification_commands"], ["custom test command"])
        self.assertEqual(failed_ci["source_ref"], source_ref)
        self.assertTrue(detect_calls)
        self.assertTrue(any(argv[:3] == ["git", "ls-tree", "-r"] for argv in calls))

    def test_symbol_source_evidence_returns_empty_when_symbol_not_declared(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_file = repo / "lib.py"
            source_file.write_text("def existing_func(): pass\n", encoding="utf-8")

            from night_shift_queue import QueueEvidenceIndex
            index = QueueEvidenceIndex(repo, {
                "tracked_files": ["lib.py"],
                "source_files": ["lib.py"],
                "test_files": [],
                "coverage_test_files": [],
            })
            evidence = index.symbol_source_evidence("lib.py", "nonexistent_symbol")

            self.assertEqual(evidence, {})

if __name__ == "__main__":
    unittest.main()
