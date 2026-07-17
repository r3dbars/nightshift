import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_sandbox import dependency_prepare_command, read_sandbox_artifact


class SandboxArtifactTests(unittest.TestCase):
    def test_reads_only_bounded_single_link_regular_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            regular = root / "regular.txt"
            regular.write_bytes(b"proof")
            self.assertEqual(read_sandbox_artifact(regular, 10), b"proof")
            self.assertIsNone(read_sandbox_artifact(regular, 2))

            target = root / "target.txt"
            target.write_bytes(b"secret")
            symlink = root / "symlink.txt"
            symlink.symlink_to(target)
            self.assertIsNone(read_sandbox_artifact(symlink, 20))

            hardlink = root / "hardlink.txt"
            os.link(target, hardlink)
            self.assertIsNone(read_sandbox_artifact(hardlink, 20))

            fifo = root / "fifo"
            os.mkfifo(fifo)
            self.assertIsNone(read_sandbox_artifact(fifo, 20))

    def test_dependency_setup_never_runs_repo_generators_or_install_scripts(self):
        command = dependency_prepare_command(
            Path("/repo"), Path("/cache"), "sha256:" + "a" * 64
        )
        script = command[-2]
        self.assertIn("npm ci --ignore-scripts", script)
        self.assertNotIn("prisma generate", script)

    def test_artifact_reader_handles_short_os_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "proof.txt"
            artifact.write_bytes(b"proof")
            with mock.patch("night_shift_sandbox.os.read", side_effect=[b"pr", b"oof", b""]):
                self.assertEqual(read_sandbox_artifact(artifact, 10), b"proof")


if __name__ == "__main__":
    unittest.main()
