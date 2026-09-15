# Finance compatibility matrix

This rebuild uses the completed CFD Finance agent as the baseline. Multi-niche behavior is an extension of that baseline, not a replacement workflow.

| Finance capability | Multi-niche implementation | Artifact / endpoint |
|---|---|---|
| Persistent projects and resume | Preserved in the local agent; each project also stores `domain_pack` and `style_id` | `ProjectStore`, `/api/projects`, `pipeline.json` |
| Background job progress and recovery | Preserved for live research, LLM scripts, HeyGen and publishing | `JobManager`, `/api/jobs/:id`, `data/jobs.json` |
| Research table with channel, source URL and metrics | Preserved; the same normalized contract applies to every domain | `/api/research`, `selected_video.json` |
| Exactly three scripts | Preserved; each candidate adds domain proof types, compliance and disclaimer | `script_candidates.json` |
| Hook/body/visual/CTA analysis and claim check | Preserved; claim rules are selected by domain, with original Finance restrictions retained | `approved_script.json`, `voice_script_heygen.txt` |
| HeyGen avatar route | Preserved with current paid-credit confirmation, polling and download | `/api/heygen`, `heygen_request.json`, `heygen_source.mp4` |
| No-face route | Preserved and generalized by selected style/domain | `/api/noface`, `noface_plan.json` |
| Raw upload/edit-only route | Preserved | `/api/upload`, `uploads/` |
| Finance Editorial edit request | Preserved as the `editorial-proof` baseline and generalized to eighteen styles | `/api/edit-request`, `EDIT_REQUEST.md`, `edit_request.json`, `edit_plan.json` |
| Feedback creates versions | Preserved; no approved render is overwritten | `/api/feedback`, `edit_feedback.json` |
| Full-watch QA gate | Preserved and made explicit as six required checks | `/api/qa`, `qa_report.json` |
| Publish or Skip | Preserved; publishing still requires current confirmation, Skip writes an explicit artifact | `/api/publish`, `publish.json` or `skip.json` |

## What changes by niche

Only the domain context changes: audience, research seeds, voice, proof types, compliance, disclaimer and default edit style. The workflow, approval gates, persistence, job model, source routes, versioning and publishing safety remain the Finance implementation.

## Edit-style extension

The Finance editorial system remains `editorial-proof`. Seventeen additional style routes are available. The original nine BrandFlow routes are joined by the eight verified HyperFrames styles: Swiss Pulse, Velvet Standard, Deconstructed, Maximalist Type, Data Drift, Soft Signal, Folk Frequency and Shadow Cut. Every style compiles to the same beat contract and is consumed by the renderer through `edit_plan.json`.
