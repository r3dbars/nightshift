import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_lifecycle import (
    active_autopilot,
    cancel_pending_workers,
    cleanup_candidates,
    deadline_reached,
    directory_size,
    recover_stale_autopilot,
    stop_deadline,
    stop_recorded_processes,
)


class StopDeadlineTests(unittest.TestCase):
    def test_morning_has_no_deadline(self):
        self.assertIsNone(stop_deadline("morning"))
        self.assertIsNone(stop_deadline(None))

    def test_timed_stop_computes_future_deadline(self):
        now = 1000.0
        deadline = stop_deadline("2h", now=now)
        self.assertEqual(deadline, now + 2 * 60 * 60)

    def test_deadline_reached_is_idempotent_on_stop_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            stop_file = Path(tmp) / "STOP"
            self.assertTrue(deadline_reached(100.0, stop_file, now=200.0))
            first_contents = stop_file.read_text(encoding="utf-8")
            # Calling again after the file already exists must not rewrite it.
            time.sleep(0.01)
            self.assertTrue(deadline_reached(100.0, stop_file, now=300.0))
            self.assertEqual(stop_file.read_text(encoding="utf-8"), first_contents)

    def test_deadline_not_reached_leaves_no_stop_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            stop_file = Path(tmp) / "STOP"
            self.assertFalse(deadline_reached(500.0, stop_file, now=100.0))
            self.assertFalse(stop_file.exists())

    def test_future_deadline_is_never_reached(self):
        self.assertFalse(deadline_reached(1_000_000.0, now=100.0))
        self.assertFalse(deadline_reached(None, now=100.0))


class StopRecordedProcessesTests(unittest.TestCase):
    def test_missing_process_file_reports_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(stop_recorded_processes(Path(tmp)), (0, 0))

    def test_malformed_rows_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            (ledger / "processes.tsv").write_text(
                "\nnot-a-pid\tfoo\tbar\n   \n", encoding="utf-8"
            )
            self.assertEqual(stop_recorded_processes(ledger), (0, 0))

    def test_system_and_current_process_group_ids_are_never_signalled(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            (ledger / "processes.tsv").write_text(
                "0\t0\tcurrent process group\n1\t0\tinit process\n", encoding="utf-8"
            )
            self.assertEqual(stop_recorded_processes(ledger), (0, 0))

    def test_missing_pid_is_counted_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            (ledger / "processes.tsv").write_text("99999999\t0\tsleep 1\n", encoding="utf-8")
            stopped, missing = stop_recorded_processes(ledger)
            self.assertEqual((stopped, missing), (0, 1))

    def test_recovery_scope_does_not_signal_stale_recorded_pid(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            (ledger / "processes.tsv").write_text("1234\t100\told worker\n", encoding="utf-8")
            with patch("night_shift_lifecycle.os.killpg") as killpg:
                stopped, missing = stop_recorded_processes(
                    ledger, not_before=1_000, now=1_000
                )
            self.assertEqual((stopped, missing), (0, 1))
            killpg.assert_not_called()


class DirectorySizeAndCleanupTests(unittest.TestCase):
    def test_directory_size_sums_file_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("1234", encoding="utf-8")
            sub = root / "sub"
            sub.mkdir()
            (sub / "b.txt").write_text("12345678", encoding="utf-8")
            self.assertEqual(directory_size(root), 12)

    def test_cleanup_candidates_requires_completion_and_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = time.time()

            old_done = root / "night-shift-old-done"
            old_done.mkdir()
            (old_done / "morning.md").write_text("done\n", encoding="utf-8")
            (old_done / "REVIEWED").write_text("yes\n", encoding="utf-8")
            os.utime(old_done, (now - 30 * 86400, now - 30 * 86400))

            old_unreviewed = root / "night-shift-old-unreviewed"
            old_unreviewed.mkdir()
            (old_unreviewed / "morning.md").write_text("done\n", encoding="utf-8")
            os.utime(old_unreviewed, (now - 30 * 86400, now - 30 * 86400))

            old_incomplete = root / "night-shift-old-incomplete"
            old_incomplete.mkdir()
            (old_incomplete / "REVIEWED").write_text("yes\n", encoding="utf-8")
            os.utime(old_incomplete, (now - 30 * 86400, now - 30 * 86400))

            recent_done = root / "night-shift-recent-done"
            recent_done.mkdir()
            (recent_done / "morning.md").write_text("done\n", encoding="utf-8")
            (recent_done / "REVIEWED").write_text("yes\n", encoding="utf-8")

            not_a_ledger = root / "other-dir"
            not_a_ledger.mkdir()

            self.assertEqual(cleanup_candidates(root, 21, now=now), [old_done])

    def test_cleanup_candidates_missing_root_returns_empty(self):
        self.assertEqual(cleanup_candidates(Path("/does/not/exist"), 21), [])


class ActiveAutopilotTests(unittest.TestCase):
    def test_missing_state_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(active_autopilot(Path(tmp) / "missing.json"), {})

    def test_stale_pid_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "active.json"
            state_path.write_text(json.dumps({"pid": 99999999}), encoding="utf-8")
            self.assertEqual(active_autopilot(state_path), {})

    def test_active_pid_is_returned(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "active.json"
            state = {"pid": os.getpid(), "mode": "night-shift"}
            state_path.write_text(json.dumps(state), encoding="utf-8")
            self.assertEqual(active_autopilot(state_path), state)


class CrashRecoveryTests(unittest.TestCase):
    def test_recovers_stale_ledger_and_marks_morning_yellow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "overnight"
            ledger = root / "night-shift-old-autopilot"
            ledger.mkdir(parents=True)
            (ledger / "morning.md").write_text("Status: GREEN\n\nOld result\n", encoding="utf-8")
            state = Path(tmp) / "active.json"
            state.write_text(json.dumps({"pid": 99999999, "ledger": str(ledger)}), encoding="utf-8")

            result = recover_stale_autopilot(state, root)

            self.assertEqual(result["status"], "recovered")
            self.assertFalse(state.exists())
            self.assertTrue((ledger / "STOP").exists())
            self.assertEqual(json.loads((ledger / "crash-recovery.json").read_text())["status"], "RECOVERED_AFTER_CRASH")
            morning = (ledger / "morning.md").read_text()
            self.assertIn("Status: YELLOW", morning)
            self.assertIn("previous controller stopped unexpectedly", morning)

    def test_refuses_stale_state_pointing_outside_ledger_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "overnight"
            root.mkdir()
            outside = Path(tmp) / "night-shift-outside"
            outside.mkdir()
            state = Path(tmp) / "active.json"
            state.write_text(json.dumps({"pid": 99999999, "ledger": str(outside)}), encoding="utf-8")

            result = recover_stale_autopilot(state, root)

            self.assertEqual(result["status"], "unsafe")
            self.assertTrue(state.exists())
            self.assertFalse((outside / "STOP").exists())

    def test_refuses_symlinked_active_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.json"
            target.write_text("{}\n", encoding="utf-8")
            state = root / "active.json"
            state.symlink_to(target)
            self.assertEqual(recover_stale_autopilot(state, root)["status"], "unsafe")

    def test_live_controller_state_is_not_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "overnight"
            ledger = root / "night-shift-live-autopilot"
            ledger.mkdir(parents=True)
            state = Path(tmp) / "active.json"
            state.write_text(json.dumps({"pid": os.getpid(), "ledger": str(ledger)}), encoding="utf-8")

            result = recover_stale_autopilot(state, root)

            self.assertEqual(result["status"], "active")
            self.assertTrue(state.exists())
            self.assertFalse((ledger / "STOP").exists())

    def test_refuses_symlinked_crashed_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "overnight"
            root.mkdir()
            real = root / "night-shift-real-autopilot"
            real.mkdir()
            ledger = root / "night-shift-link-autopilot"
            ledger.symlink_to(real, target_is_directory=True)
            state = Path(tmp) / "active.json"
            state.write_text(json.dumps({"pid": 99999999, "ledger": str(ledger)}), encoding="utf-8")

            self.assertEqual(recover_stale_autopilot(state, root)["status"], "unsafe")
            self.assertFalse((real / "STOP").exists())


class CancelPendingWorkersIntegrationTests(unittest.TestCase):
    def test_cancels_real_process_group_and_pending_futures(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            process = subprocess.Popen(["sleep", "30"], start_new_session=True)
            try:
                (ledger / "processes.tsv").write_text(
                    f"{process.pid}\t0\tsleep 30\n", encoding="utf-8"
                )

                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                # Occupy the sole worker so the second future stays queued and
                # therefore cancellable, mirroring real pending-worker futures.
                occupied = executor.submit(time.sleep, 1)
                pending_future = executor.submit(time.sleep, 30)
                pending = {pending_future}

                cancel_pending_workers(ledger, pending)
                process.wait(timeout=2)

                self.assertNotEqual(process.returncode, 0)
                self.assertNotEqual(process.poll(), None)
                self.assertTrue(pending_future.cancelled())
                executor.shutdown(wait=False, cancel_futures=True)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()

    def test_no_pending_processes_or_futures_is_a_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            cancel_pending_workers(ledger, [])


if __name__ == "__main__":
    unittest.main()
