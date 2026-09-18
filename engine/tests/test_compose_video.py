import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import compose_video


class ComposeVideoTests(unittest.TestCase):
    def test_drawtext_apostrophe_does_not_break_filter_quotes(self):
        escaped = compose_video.escape_drawtext("startup 'AnimAI'")
        self.assertEqual(escaped, "startup ’AnimAI’")
        self.assertNotIn("'", escaped)


if __name__ == "__main__":
    unittest.main()
