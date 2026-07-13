import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_models import output_token_budget


class ModelBudgetTests(unittest.TestCase):
    def test_reasoning_models_get_room_for_visible_output(self):
        self.assertEqual(output_token_budget("qwen3.5-35b-a3b", 1536), 8192)
        self.assertEqual(output_token_budget("deepseek-r1-distilled", 4096), 8192)

    def test_regular_models_keep_the_requested_budget(self):
        self.assertEqual(output_token_budget("phi-4-mini-instruct", 1536), 1536)
        self.assertEqual(output_token_budget("qwen2.5-coder", 4096), 4096)


if __name__ == "__main__":
    unittest.main()
