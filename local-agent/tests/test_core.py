import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_core


class CoreFlowTests(unittest.TestCase):
    def test_all_upstream_and_brandflow_styles_are_available(self):
        styles = agent_core.load_edit_styles()
        self.assertGreaterEqual(len(styles), 18)
        self.assertTrue({"editorial-proof", "swiss-pulse", "shadow-cut"}.issubset({item["id"] for item in styles}))

    def test_demo_research_has_required_columns(self):
        rows = agent_core.demo_research(["facebook", "tiktok", "youtube"], "forex", "")
        self.assertEqual(len(rows), 3)
        required = {"platform", "url", "views", "likes", "comments", "shares", "viral_score", "viral_reason"}
        self.assertTrue(required.issubset(rows[0]))

    def test_keyword_filter(self):
        rows = agent_core.demo_research(["youtube"], "forex", "liquidity")
        self.assertEqual(len(rows), 1)
        self.assertIn("Liquidity", rows[0]["title"])

    def test_three_scripts_and_claim_check(self):
        video = {"title": "Liquidity Pool"}
        scripts = agent_core.demo_scripts(video, {"cta": "Theo dõi kênh."})
        self.assertEqual(len(scripts), 3)
        self.assertTrue(all(item["analysis"].get("hook") for item in scripts))
        warning = agent_core.check_claims("Cam kết lợi nhuận 100% và mua ngay")
        self.assertTrue(any(item["level"] == "warning" for item in warning))

    def test_noface_plan_is_persisted(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            plan = agent_core.create_noface_plan(folder, {"scenes": [{"text": "Hook"}]})
            self.assertEqual(plan["route"], "no-face")
            self.assertTrue((folder / "noface_plan.json").exists())

    def test_non_finance_domain_uses_domain_pack(self):
        rows = agent_core.demo_research(["youtube"], "real-estate", "")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["industry"], "real-estate")
        scripts = agent_core.demo_scripts(rows[0], {"cta": "Theo dõi."}, "real-estate")
        self.assertEqual(len(scripts), 3)
        self.assertIn("location-map", scripts[0]["analysis"]["visual"])

    def test_edit_plan_has_required_beat_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            agent_core.write_json(folder / "approved_script.json", {"text": "Hook rõ ràng. Bằng chứng cụ thể. Theo dõi kênh."})
            plan = agent_core.build_edit_plan(folder, {"style_id": "tiktok-creator", "target_seconds": 45}, "ecommerce")
            required = {"start", "end", "spoken_meaning", "visual_role", "asset_source", "caption_treatment", "text_effect", "transition", "audio_cue", "fallback"}
            self.assertEqual(plan["style"]["id"], "tiktok-creator")
            self.assertTrue(all(required.issubset(beat) for beat in plan["beats"]))
            self.assertTrue((folder / "edit_plan.json").exists())

    def test_edit_plan_routes_context_stock_from_pexels_to_pixabay(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            agent_core.write_json(folder / "approved_script.json", {"text": "Hook rõ ràng. Mỗi ngày khách hàng làm việc qua ba công cụ. Báo cáo cho thấy chi phí tăng 25%. Theo dõi kênh."})
            plan = agent_core.build_edit_plan(folder, {"style_id": "warm-story", "video_mode": "upload", "target_seconds": 45}, "ecommerce")
            context = next(beat for beat in plan["beats"] if beat["visual_role"] == "context")
            self.assertEqual(context["stock_providers"], ["pexels", "pixabay"])
            self.assertEqual(context["source_order"][:3], ["owned-assets", "pexels", "pixabay"])
            self.assertTrue(all(not beat["stock_providers"] for beat in plan["beats"] if beat["visual_role"] != "context"))

    def test_voice_alignment_replaces_equal_beat_timing(self):
        plan = {
            "beats": [
                {"id": "beat-1", "start": 0, "end": 5},
                {"id": "beat-2", "start": 5, "end": 10},
            ]
        }
        timestamps = [
            {"start": 0.42, "end": 2.15, "alignment_mode": "matched", "match_score": 0.91},
            {"start": 2.31, "end": 7.84, "alignment_mode": "proportional", "match_score": 0.35},
        ]

        result = agent_core._apply_voice_timing(plan, timestamps, 8.0)

        self.assertEqual(result["beats"][0]["start"], 0.42)
        self.assertEqual(result["beats"][1]["end"], 7.84)
        self.assertEqual(result["beats"][1]["timing_source"], "voice-alignment")
        self.assertEqual(result["voice_aligned_beats"], 2)

    def test_qa_requires_every_check_and_explicit_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            keys = ["full_watch", "caption_safe_area", "voice_alignment", "no_flash_frames", "source_traceability", "claims_checked"]
            report = agent_core.build_qa_report(folder, {"checks": {key: True for key in keys}, "approved": True}, "finance")
            self.assertTrue(report["approved"])
            self.assertTrue((folder / "qa_report.json").exists())


if __name__ == "__main__":
    unittest.main()
