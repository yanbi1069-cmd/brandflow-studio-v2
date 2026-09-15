# Architecture

```text
Browser studio
  ├─ Brand Memory (localStorage)
  ├─ Research UI ───── POST /api/research ───── Apify | demo fallback
  ├─ Script editor ─── POST /api/generate-script ─ Kyma | demo fallback
  └─ Production UI ─── POST /api/pipeline ───── manifest.json
                                                    │
Local engine                                        ▼
  run_pipeline.py → job folder → HeyGen/source video
       → Whisper alignment → captions → semantic edit plan
       → owned assets / designed proof / Pexels → Pixabay fallback
       → ffmpeg compose → full-watch QA → final.mp4
```

The split is deliberate: Vercel is suitable for the interactive studio and lightweight API requests, while Whisper and FFmpeg rendering are long-running local workloads. It also prevents a public demo from spending HeyGen credits without explicit action.

## Data boundaries

- Browser: draft brand configuration and script only.
- Server: API keys only via environment variables.
- Local engine: media assets and final renders under `workspace/jobs/`.
- Repository: code, presets, examples and documentation; never credentials.

## B-roll boundary

- The approved audio is the timeline source of truth.
- Presenter/source video: hook, opinion, trust, transition and CTA.
- Designed visual proof: measurable or technical claims.
- Stock B-roll: context/action only; Pexels first, Pixabay second.
- If stock is weak or unavailable, return to presenter/typography instead of inserting a decorative clip.
- `media_manifest.json` records provider, source page, creator, license and the beat where the asset is used.
