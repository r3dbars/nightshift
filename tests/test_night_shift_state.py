import multiprocessing
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_state import exclusive_lock


def contend(path: str, ready, start, results) -> None:
    ready.put(os.getpid())
    start.wait()
    with exclusive_lock(Path(path)) as acquired:
        results.put((os.getpid(), acquired))
        if acquired:
            time.sleep(0.25)


class ExclusiveLockTests(unittest.TestCase):
    def test_eight_way_fanout_has_one_owner_and_clean_losers(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = multiprocessing.get_context("spawn")
            ready = ctx.Queue()
            results = ctx.Queue()
            start = ctx.Event()
            processes = [
                ctx.Process(target=contend, args=(str(Path(tmp) / "lock"), ready, start, results))
                for _ in range(8)
            ]
            for process in processes:
                process.start()
            for _ in processes:
                ready.get(timeout=5)
            start.set()
            rows = [results.get(timeout=5) for _ in processes]
            for process in processes:
                process.join(timeout=5)
                self.assertEqual(process.exitcode, 0)
            self.assertEqual(sum(acquired for _, acquired in rows), 1)

    def test_crash_releases_kernel_lock_without_deleting_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lock"
            ctx = multiprocessing.get_context("spawn")
            ready = ctx.Queue()
            start = ctx.Event()
            results = ctx.Queue()
            owner = ctx.Process(target=contend, args=(str(path), ready, start, results))
            owner.start()
            ready.get(timeout=5)
            start.set()
            self.assertTrue(results.get(timeout=5)[1])
            owner.kill()
            owner.join(timeout=5)
            with exclusive_lock(path) as acquired:
                self.assertTrue(acquired)
            self.assertTrue(path.is_file())

    def test_stale_legacy_directory_is_migrated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lock"
            path.mkdir()
            (path / "pid").write_text("99999999\n", encoding="utf-8")
            with exclusive_lock(path) as acquired:
                self.assertTrue(acquired)
            self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
