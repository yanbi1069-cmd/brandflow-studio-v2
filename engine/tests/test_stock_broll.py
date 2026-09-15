import json
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import compose_video
import stock_broll
import technical_broll


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
            self.assertEqual(len(manifest["fallbacks"]), 2)
            context_plan = next(item for item in manifest["fallbacks"] if item["beat_id"] == "life")
            proof_plan = next(item for item in manifest["fallbacks"] if item["beat_id"] == "proof")
            self.assertEqual(context_plan["provider_order"], ["pexels", "pixabay"])
            self.assertEqual(context_plan["status"], "planned-stock")
            self.assertEqual(proof_plan["status"], "planned-technical-motion")
            self.assertEqual(json.loads((root / "broll_slots.json").read_text())["slots"], [])

    def test_semantic_query_uses_concrete_english_visual(self):
        query, intent = stock_broll.semantic_stock_query(
            {"spoken_meaning": "Tôi từ từ đẩy ly nước cho đến khi nó chạm mép bàn."},
            "forex",
        )
        self.assertEqual(intent, "physical-metaphor")
        self.assertIn("glass of water", query)
        self.assertNotIn("từ từ", query)

    def test_finance_claim_selects_market_motion_graphic(self):
        kind = technical_broll.classify_visual({
            "spoken_meaning": "Giá vàng lao dốc rồi phục hồi vì áp lực thanh khoản ngắn hạn.",
            "asset_source": "before-after",
        })
        self.assertEqual(kind, "market-chart")

    def test_abstract_claim_does_not_get_unrelated_stock(self):
        query, intent = stock_broll.semantic_stock_query(
            {"spoken_meaning": "Không nên bán tháo khi chưa hiểu nguyên nhân."},
            "finance",
        )
        self.assertEqual((query, intent), ("", "no-concrete-visual"))

    def test_water_glass_metaphor_is_illustrated_locally(self):
        kind = technical_broll.classify_visual({
            "spoken_meaning": "Tôi từ từ đẩy ly nước đến mép bàn mà không đổ."
        })
        self.assertEqual(kind, "glass-metaphor")

    def test_news_claim_uses_signal_visual_not_repeated_market_chart(self):
        kind = technical_broll.classify_visual({
            "spoken_meaning": "Tin NFP mạnh bất ngờ nhưng xu hướng vẫn tăng."
        })
        self.assertEqual(kind, "signal-dashboard")

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
