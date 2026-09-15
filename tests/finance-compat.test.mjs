import assert from "node:assert/strict";
import test from "node:test";
import domains from "../config/domain-packs.json" with { type: "json" };
import styles from "../config/edit-styles-v2.json" with { type: "json" };
import { buildEditPlan, buildFinanceCompatibleScripts, demoResearchRows } from "../lib/finance-core-compat.js";

test("research keeps the complete Finance table contract in every niche", () => {
  const rows = demoResearchRows({ niche: "bất động sản", platforms: ["youtube", "tiktok", "facebook"] });
  const fields = ["channel", "platform", "title", "url", "views", "likes", "comments", "shares", "engagementPct", "viralScore", "viralReason"];
  assert.ok(rows.length >= 3);
  rows.forEach((row) => fields.forEach((field) => assert.ok(Object.hasOwn(row, field), `${field} missing`)));
});

test("every domain produces exactly three Finance-compatible scripts", () => {
  domains.forEach((domain) => {
    const scripts = buildFinanceCompatibleScripts({ video: { title: "Chủ đề thử" }, brand: { name: "Brand", niche: domain.niche, audience: domain.audience }, domain, format: { id: "evidence-explainer" } });
    assert.equal(scripts.length, 3);
    scripts.forEach((script) => {
      assert.ok(script.text && script.analysis?.hook && script.analysis?.visual);
      assert.ok(Array.isArray(script.claimCheck) && script.claimCheck.length);
    });
  });
});

test("all edit styles compile to the full beat contract", () => {
  const domain = domains.find((item) => item.id === "finance");
  const script = { hook: "Hook rõ.", body: "Bằng chứng thứ nhất. Hành động thứ hai.", cta: "Theo dõi kênh." };
  const required = ["start", "end", "spokenMeaning", "visualRole", "assetSource", "captionTreatment", "textEffect", "transition", "audioCue", "fallback"];
  styles.forEach((style) => {
    const plan = buildEditPlan({ script, style, domain });
    assert.equal(plan.styleId, style.id);
    assert.ok(plan.beats.length >= 4);
    plan.beats.forEach((beat) => required.forEach((field) => assert.ok(Object.hasOwn(beat, field), `${style.id}.${field} missing`)));
  });
});

test("edit plan uses semantic visual roles and Pexels to Pixabay fallback only for context", () => {
  const domain = domains.find((item) => item.id === "finance");
  const style = styles.find((item) => item.id === "warm-story");
  const script = {
    hook: "Tôi muốn bạn nhớ điều này.",
    body: "Mỗi ngày khách hàng phải làm việc qua ba công cụ. Báo cáo cho thấy chi phí tăng 25%. Hãy hình dung quy trình như một nút thắt. Đây là quan điểm của tôi.",
    cta: "Theo dõi kênh để xem thêm.",
  };
  const plan = buildEditPlan({ script, style, domain, videoMode: "upload" });
  assert.deepEqual(plan.beats.map((beat) => beat.visualRole), ["presenter", "context", "proof", "metaphor", "presenter", "presenter"]);
  const context = plan.beats.find((beat) => beat.visualRole === "context");
  assert.deepEqual(context.stockProviders, ["pexels", "pixabay"]);
  assert.deepEqual(context.sourceOrder.slice(0, 3), ["owned-assets", "pexels", "pixabay"]);
  assert.ok(plan.beats.filter((beat) => beat.visualRole !== "context").every((beat) => beat.stockProviders.length === 0));
  assert.equal(plan.verification.semanticCutsOnly, true);
});
