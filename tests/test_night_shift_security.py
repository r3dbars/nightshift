import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_redaction import contains_secret, context_path_is_sensitive, redact


class SecretRedactionTests(unittest.TestCase):
    def test_redacts_common_secret_formats(self):
        samples = [
            "Authorization: Bearer abcdefghijklmnopqrstuvwxyz",
            "github_pat_abcdefghijklmnopqrstuvwxyz123456",
            "ghp_abcdefghijklmnopqrstuvwxyz123456",
            "AKIAABCDEFGHIJKLMNOP",
            "xox" + "b-1234567890-abcdefghijklmnop",
            "eyJabcdefghijk.abcdefghijklmnop.abcdefghijklmnop",
            "client_secret='abcdefghijklmnopqrstuvwxyz'",
            "-----BEGIN PRIVATE KEY-----\nabc123\n-----END PRIVATE KEY-----",
        ]
        for sample in samples:
            with self.subTest(sample=sample[:20]):
                self.assertTrue(contains_secret(sample))
                self.assertNotIn(sample, redact(sample))
                self.assertIn("[REDACTED_SECRET]", redact(sample))

    def test_sensitive_context_paths_are_rejected(self):
        for path in (
            ".env", ".env.local", ".ssh/id_rsa", ".aws/credentials",
            "config/private.key", "../outside", "/tmp/secret.txt",
        ):
            with self.subTest(path=path):
                self.assertTrue(context_path_is_sensitive(path))
        self.assertFalse(context_path_is_sensitive("src/auth.py"))
        self.assertFalse(context_path_is_sensitive("tests/test_auth.py"))


if __name__ == "__main__":
    unittest.main()
