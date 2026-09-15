import json
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import compose_video
import stock_broll


class StockBrollTests(unittest.TestCase):
    def test_dry_run_only_plans_context_beats(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan = {"beats": [
                {"id": "hook", "start": 0, "end": 3, "visualRole": "presenter", "spokenMeaning": "Hook"},
                {"id": "life", "start": 3, "end": 6, "visualRole": "context", "spokenMeaning": "Mỗi ngày khách hàng làm việc", "stockProviders": ["pexels", "pixabay"]},
                {"id": "proof", "start": 6, "end": 10, "visualRole": "proof", "spokenMeaning": "Số liệu"},
            ]}
            edit_plan = root / "edit_plan.json"
            edit_plan.write_text(json.dumps(plan), encoding="utf-8")
            manifest = stock_broll.prepare_context_broll(edit_plan, root / "media", root / "broll_slots.json", root / "media_manifest.json", dry_run=True)
            self.assertEqual(len(manifest["fallbacks"]), 1)
            self.assertEqual(manifest["fallbacks"][0]["provider_order"], ["pexels", "pixabay"])
            self.assertEqual(json.loads((root / "broll_slots.json").read_text())["slots"], [])

    def test_renderer_resolves_pixabay_and_stock_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            media = Path(temp)
            (media / "pixabay").mkdir()
            clip = media / "pixabay" / "life.mp4"
            clip.write_bytes(b"test")
            self.assertEqual(Path(compose_video.find_broll_source("life", str(media), "pixabay")), clip)
            self.assertEqual(Path(compose_video.find_broll_source("life", str(media), "stock")), clip)


if __name__ == "__main__":
    unittest.main()
