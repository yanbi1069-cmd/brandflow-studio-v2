import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "transcribe_align_news.py"
SPEC = importlib.util.spec_from_file_location("transcribe_align_news", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SubtitleAlignmentTests(unittest.TestCase):
    def test_mismatched_phrase_uses_proportional_fallback(self):
        words = [
            {"token": token, "raw": token, "start": index * 0.4, "end": index * 0.4 + 0.35}
            for index, token in enumerate("gia vang dang bien dong manh nha dau tu can quan sat".split())
        ]
        phrases = [
            {"spoken": "Một câu hoàn toàn khác transcript", "display": "Một câu hoàn toàn khác transcript"},
            {"spoken": "Nhà đầu tư cần quan sát", "display": "Nhà đầu tư cần quan sát"},
        ]

        aligned = MODULE.align_phrases(words, phrases)

        self.assertEqual(len(aligned), 2)
        self.assertEqual(aligned[0]["alignment_mode"], "proportional")
        self.assertGreater(aligned[0]["end"], aligned[0]["start"])
        self.assertGreater(aligned[1]["start"], aligned[0]["start"])

    def test_empty_transcript_has_friendly_error(self):
        with self.assertRaisesRegex(RuntimeError, "Không nhận diện được lời nói"):
            MODULE.align_phrases([], [{"spoken": "Xin chào", "display": "Xin chào"}])


if __name__ == "__main__":
    unittest.main()
