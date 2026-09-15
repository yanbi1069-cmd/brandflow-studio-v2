# Personal Brand Video Agent V2 — full system

## Two delivery surfaces

- The Vercel studio at `/multi-niche` is the course-ready product and safe planning UI. It runs demo/live adapters, stores draft state in the browser and exports a complete project package without silently spending credits or publishing.
- `local-agent/` is the production runner inherited from the Finance agent. It persists binary files and jobs, calls HeyGen only after confirmation, accepts uploads, hands off edit work, records QA and can run the existing publishers.

## End-to-end workflow

1. Select entry mode: full pipeline, script-first, edit-only or publish-only.
2. Select a domain pack and content format.
3. Research Facebook, TikTok and YouTube; compare channel, original URL, views, likes, comments, shares, engagement and viral hypothesis.
4. Approve one reference video.
5. Generate exactly three original scripts, inspect creative analysis and claim check, then approve one.
6. Choose HeyGen Avatar, No-face or Upload.
7. Select one of eighteen edit styles and compile a beat-level edit plan.
8. Render/hand off the edit, keep feedback in versioned rounds and never overwrite an approved file.
9. Complete full-watch QA and approve the final.
10. Export locally or publish after a separate current confirmation.

## Run locally

Web studio:

```powershell
npm install
npm run dev
```

Production local agent:

```powershell
cd local-agent
python -m pip install -r requirements.txt
python start_agent.py
```

Open `http://127.0.0.1:8765/`.

## Data boundaries

- The untouched Finance reference pack is stored under `reference-packs/CFD-Finance-Agent-Reference-Pack/`.
- The runnable generalized copy is under `local-agent/`.
- New jobs are stored under `local-agent/workspace/content/` or `workspace/jobs/`.
- Reference video/audio, local credentials, job data and archives are excluded from Vercel deployment by `.vercelignore`.
- `.env` remains local and must never be committed or exported in a project package.
