import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import Mock, patch

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

    def test_noface_uploaded_voice_becomes_render_source(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            uploads = folder / "uploads"
            uploads.mkdir()
            (uploads / "voice-test.mp3").write_bytes(b"audio")
            result = agent_core.prepare_noface_source(folder, {"voice_source": "recorded", "source_file": "uploads/voice-test.mp3", "scenes": [{"text": "Hook"}]}, lambda *_: None)
            self.assertEqual(result["file"], "uploads/voice-test.mp3")
            self.assertEqual(result["plan"]["status"], "ready")

    def test_noface_tts_creates_audio_source(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            agent_core.write_json(folder / "approved_script.json", {"text": "Xin chào BrandFlow."})
            def fake_run(command, **_kwargs):
                Path(command[-1]).write_bytes(b"audio")
                return agent_core.subprocess.CompletedProcess(command, 0, "", "")
            with patch.object(agent_core.subprocess, "run", side_effect=fake_run):
                result = agent_core.prepare_noface_source(folder, {"voice_source": "tts", "voice": "vi-VN-HoaiMyNeural"}, lambda *_: None)
            self.assertEqual(result["file"], "noface_voice.mp3")
            self.assertEqual(result["plan"]["status"], "ready")

    def test_noface_approved_audio_uses_heygen_voice_id(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            agent_core.write_json(folder / "approved_script.json", {"text": "Xin chào BrandFlow."})
            (folder / "heygen_source.mp4").write_bytes(b"video")
            def fake_engine(command, *_args, **_kwargs):
                Path(command[-1]).write_bytes(b"heygen-audio")
            with patch.object(agent_core, "load_secrets", return_value={"HEYGEN_API_KEY": "secret", "HEYGEN_VOICE_ID": "voice-1", "HEYGEN_AVATAR_ID": "avatar-1"}), patch.object(agent_core, "submit_heygen", return_value={"file": "heygen_source.mp4"}), patch.object(agent_core, "_run_engine", side_effect=fake_engine):
                result = agent_core.prepare_noface_source(folder, {"voice_source": "approved-audio"}, lambda *_: None)
            self.assertEqual(result["file"], "heygen_voice.mp3")
            self.assertEqual(result["plan"]["voice_provider"], "heygen")
            self.assertEqual(result["plan"]["voice_id"], "***")

    def test_completed_render_is_reused_on_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / "voice.mp3").write_bytes(b"audio")
            (folder / "final-v1.mp4").write_bytes(b"video")
            agent_core.write_json(folder / "render_qa-v1.json", {"technical_ok": True})
            agent_core.write_json(folder / "edit_plan-v1.json", {"version": 1})
            result = agent_core.render_edit(folder, {"source_file": "voice.mp3", "version": 1}, lambda *_: None, "finance")
            self.assertTrue(result["resumed"])
            self.assertEqual(result["file"], "final-v1.mp4")

    def test_retry_opens_latest_completed_render(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / "voice.mp3").write_bytes(b"audio")
            for version in (1, 2):
                (folder / f"final-v{version}.mp4").write_bytes(b"video")
                agent_core.write_json(folder / f"render_qa-v{version}.json", {"technical_ok": True})
                agent_core.write_json(folder / f"edit_plan-v{version}.json", {"version": version})
            result = agent_core.render_edit(folder, {"source_file": "voice.mp3", "version": 1}, lambda *_: None, "finance")
            self.assertEqual(result["file"], "final-v2.mp4")
            self.assertEqual(result["version"], 2)

    def test_completed_render_is_reused_only_for_the_selected_style(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            for version, style_id in ((1, "editorial-proof"), (2, "warm-story")):
                (folder / f"final-v{version}.mp4").write_bytes(b"video")
                agent_core.write_json(folder / f"render_qa-v{version}.json", {"technical_ok": True})
                agent_core.write_json(folder / f"edit_plan-v{version}.json", {"style": {"id": style_id}})
            self.assertEqual(agent_core.latest_reusable_render_version(folder, 1, "editorial-proof"), 1)
            self.assertEqual(agent_core.latest_reusable_render_version(folder, 1, "warm-story"), 2)
            self.assertIsNone(agent_core.latest_reusable_render_version(folder, 1, "data-kinetic"))

    def test_noface_plan_assigns_a_visual_role_to_every_beat(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            agent_core.write_json(folder / "approved_script.json", {"text": "Bạn có biết sai lầm này? Một nhóm startup đang làm việc mỗi ngày. Theo dõi để xem thêm."})
            plan = agent_core.build_edit_plan(folder, {"video_mode": "noface", "target_seconds": 15}, "finance")
            self.assertTrue(plan["verification"]["full_visual_coverage_required"])
            self.assertNotIn("presenter", {beat["visual_role"] for beat in plan["beats"]})

    def test_overlay_uses_a_complete_meaningful_clause(self):
        value = agent_core.meaningful_overlay_text("Hãy nhìn biểu đồ này: đường màu đỏ là chi phí GPU tăng 300% từ 2022 đến 2024.")
        self.assertEqual(value, "đường màu đỏ là chi phí GPU tăng 300% từ 2022 đến 2024")

    def test_overlay_keeps_the_claim_after_a_short_lead_in(self):
        value = agent_core.meaningful_overlay_text("Nhưng đến tháng 6/2024, theo báo cáo của PitchBook, giá trị giảm 60%.")
        self.assertIn("PitchBook", value)
        self.assertIn("giảm 60%", value)
        self.assertNotEqual(value, "Nhưng đến tháng 6/2024")

    def test_generated_visual_suppresses_duplicate_big_overlay(self):
        manifest = {"assets": [
            {"beat_id": "beat-1", "provider": "brandflow-local", "overlay_policy": "suppress"},
            {"beat_id": "beat-2", "provider": "pexels"},
        ]}
        self.assertEqual(agent_core.overlay_suppressed_beat_ids(manifest), {"beat-1"})

    def test_numeric_advice_is_context_not_automatic_chart(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            agent_core.write_json(folder / "approved_script.json", {"text": "Hãy dành 5% danh mục và kiểm tra báo cáo. Theo báo cáo, chi phí tăng 25%. Theo dõi để xem thêm."})
            for mode in ("noface", "upload", "avatar"):
                plan = agent_core.build_edit_plan(folder, {"video_mode": mode, "target_seconds": 12}, "finance")
                self.assertEqual(plan["beats"][0]["visual_role"], "context" if mode == "noface" else "presenter")
                self.assertEqual(plan["beats"][1]["visual_role"], "proof")

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
