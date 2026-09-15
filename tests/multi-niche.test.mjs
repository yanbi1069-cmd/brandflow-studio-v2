import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";

const readJson = async (relative) => JSON.parse(await readFile(new URL(relative, import.meta.url), "utf8"));

test("domain packs are reusable and keep compliance decisions", async () => {
  const domains = await readJson("../config/domain-packs.json");
  assert.ok(domains.length >= 8);
  assert.equal(new Set(domains.map((item) => item.id)).size, domains.length);
  domains.forEach((item) => {
    assert.ok(item.defaultStyle);
    assert.ok(item.proofTypes.length >= 3);
    assert.ok(item.compliance.length >= 2);
  });
});

test("content formats define a full narrative route", async () => {
  const formats = await readJson("../config/content-formats.json");
  assert.ok(formats.length >= 8);
  formats.forEach((item) => assert.ok(item.structure.length >= 4));
});

test("v2 edit styles include diverse motion grammar", async () => {
  const styles = await readJson("../config/edit-styles-v2.json");
  assert.ok(styles.length >= 18);
  styles.forEach((item) => {
    assert.equal(item.palette.length, 3);
    assert.ok(item.textEffects.length >= 2);
    assert.ok(item.transitions.length >= 2);
    assert.ok(item.brollPriority.length >= 3);
  });
});
