---
name: brandflow-video-studio
description: Vận hành sản phẩm BrandFlow để research, viết kịch bản, chuẩn bị avatar/no-face, chọn phong cách edit và QA video thương hiệu cá nhân. Dùng khi người dùng muốn tạo hoặc hoàn thiện video ngắn bằng pipeline trong project Build To Own; không dùng cho đăng bài tự động.
---

# BrandFlow Video Studio

Work in `brandflow-studio/`. Preserve the original course folders and source agents; every new project artifact belongs under `brandflow-studio/workspace/jobs/`.

## Operating contract

1. Collect or infer brand name, niche, audience, voice, topic, CTA, avatar/voice choice and target platform.
2. Research first. Use a real source only when the user authorizes available API access; otherwise use demo data and label it honestly.
3. Treat reference content as evidence and structural inspiration. Never copy its wording or unique examples.
4. Get script approval before any paid avatar generation.
5. Select an edit style from `brandflow-studio/config/edit-styles.json`. Default to `editorial-proof` for technical, finance or educational claims.
6. Download/create a manifest in the studio, then prepare the local job with `brandflow-studio/engine/run_pipeline.py`.
7. For local rendering, read `brandflow-studio/engine/PRODUCTION.md`. For finance/expert editorial work, also read `brandflow-studio/engine/reference/finance-editorial/README_FOR_AGENT.md` and `QA_CHECKLIST.md`.
8. Inspect the full render and scene boundaries before calling a video complete.

## Non-negotiable edit invariants

- Cut on semantic beats, not a fixed timer.
- A technical claim needs a chart, diagram or motion graphic that proves it.
- Captions follow actual speech, stay within two lines and do not cover chart labels.
- Adjacent B-roll slots share exact boundaries; no flash frames.
- Use owned brand assets first; use relevant stock footage only as supporting context.

Stop before auto-posting. Publishing is a separate authorized action.
