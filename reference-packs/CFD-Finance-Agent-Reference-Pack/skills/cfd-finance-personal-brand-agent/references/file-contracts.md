# File contracts

Each project lives under `workspace/content/YYYY-MM-DD/<slug>/`.

| Stage | Required artifact |
|---|---|
| Research selection | `selected_video.json` |
| Script candidates | `script_candidates.json` |
| Script approval | `approved_script.json`, `voice_script_heygen.txt` |
| HeyGen | `heygen_request.json`, `heygen_video_id.txt`, `heygen_source.mp4` |
| No-face | `noface_plan.json` |
| Uploaded source | `uploads/source-<filename>` |
| Edit handoff | `EDIT_REQUEST.md`, `edit_request.json` |
| Revisions | `edit_feedback.json`, versioned renders |
| Final | `final.mp4`, QA report |
| Distribution | `NOI_DUNG_DANG_BAI.txt`, `meta.json`, `publish.json` |

The edit handoff references `workspace/share/nhi-finance-editorial-training-pack`. The separate `finance-editorial-edit` skill owns the concrete editing and QA process.

