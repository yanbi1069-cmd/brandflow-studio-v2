# Local production engine

The web studio creates and downloads a production manifest. The local engine turns that manifest into a reproducible video job while keeping paid API calls under human control.

## 1. Prepare a job

```powershell
python engine/run_pipeline.py path/to/manifest.json
```

The command creates `workspace/jobs/<date-brand-topic>/` with:

- `manifest.json`
- `voice_script_heygen.txt`
- `script_scenes.json`
- `subtitle_phrases.json`
- `QA_CHECKLIST.md`

## 2. Generate the source video

Use HeyGen Studio or the account-specific API workflow to create `avatar.mp4`. Always verify that the avatar and cloned voice belong to the active brand. Never keep avatar or voice IDs as shared defaults.

## 3. Align captions

```powershell
python engine/scripts/transcribe_align_news.py <job>/avatar.mp4 <job>/subtitle_phrases.json <job>/timestamps.json <job>/captions_base.ass <job>/transcript_raw.txt
python engine/scripts/generate_captions.py <job>/timestamps.json <job>/captions.ass
```

Review any alignment score below `0.85` against the actual audio.

## 4. Prepare B-roll and visual proof

Order of preference:

1. Owned, pre-approved brand assets.
2. Technical charts, diagrams or motion graphics that prove the narration.
3. Relevant real-world footage from Pexels, with Pixabay as fallback.
4. Return to the approved source video or brand typography when neither stock provider has a relevant portrait clip.

Stock is only for a `context` beat. Keep the source presenter for the hook, opinion, transition and CTA. Use charts, screenshots, documents or designed motion graphics for `proof`; use a deliberately designed prop/action for `metaphor`. Cuts follow changes in meaning rather than a fixed time interval.

Prepare all contextual stock slots and a traceable media manifest:

```powershell
python engine/scripts/stock_broll.py <job>/edit_plan.json --media-dir <job>/media --slots <job>/broll_slots.json --manifest <job>/media_manifest.json
```

The command tries Pexels first, then Pixabay, downloads the selected clip into the job and records source page, creator, license and beat usage. Pixabay query results are cached for 24 hours. Use `--dry-run` to inspect planned queries without calling either API.

Adjacent stock/proof slots must share the same boundary. An unintended gap can expose a flash of the source video. A deliberate gap is allowed only when the edit plan says to return to the presenter.

## 5. Compose and QA

```powershell
python engine/scripts/compose_video.py <job>/avatar.mp4 <job>/broll_slots.json <job>/media <job>/captions.ass "@brand" <job>/final.mp4 <job>/text_overlays.json
```

Inspect the full render, not only still frames. The editorial reference under `engine/reference/finance-editorial/` is the approved baseline for technical/expert content.
