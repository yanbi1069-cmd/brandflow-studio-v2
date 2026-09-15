import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { buildDemoScript, tailorTrends } from "../lib/demo-data.js";

test("demo research is tailored and ranked", () => {
  const rows = tailorTrends("bất động sản");
  assert.equal(rows.length, 3);
  assert.match(rows[0].title, /bất động sản/i);
  assert.ok(rows[0].breakout >= rows[1].breakout);
});

test("demo script always returns the production contract", () => {
  const result = buildDemoScript({ niche: "spa", audience: "chủ spa", brandName: "Lumi", trendTitle: "Test" });
  assert.ok(result.hook.length > 20);
  assert.ok(result.body.length > result.hook.length);
  assert.ok(result.cta.includes("Lumi"));
  assert.equal(result.sourceMode, "demo");
});

test("every edit style has a unique id and three-color palette", async () => {
  const raw = await readFile(new URL("../config/edit-styles.json", import.meta.url), "utf8");
  const styles = JSON.parse(raw);
  assert.equal(new Set(styles.map((style) => style.id)).size, styles.length);
  assert.ok(styles.length >= 5);
  styles.forEach((style) => assert.equal(style.palette.length, 3));
});
