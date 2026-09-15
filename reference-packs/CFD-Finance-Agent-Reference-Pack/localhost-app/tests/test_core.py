import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_core


class CoreFlowTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
