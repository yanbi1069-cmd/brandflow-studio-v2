---
name: cfd-finance-personal-brand-agent
description: Orchestrate a Vietnamese CFD, trading, or finance personal-brand short-video workflow from competitor research and script selection through HeyGen or no-face production, finance-editorial editing, feedback revisions, download, and optional publishing. Use when the user wants to create, package, run, or continue this end-to-end content Agent.
---

# CFD Finance Personal Brand Agent

Operate the packaged localhost workflow and keep every human approval gate explicit.

## Route the request

1. Read [workflow.md](references/workflow.md).
2. For project artifacts and handoffs, read [file-contracts.md](references/file-contracts.md).
3. Before any HeyGen render or publish action, read [safety-and-publishing.md](references/safety-and-publishing.md).
4. If editing is requested, invoke the separate `finance-editorial-edit` skill and use the project training pack. Do not recreate its editing rules here.

## Operating rules

- Start the app with `python start_agent.py` from the packaged folder when the user wants the visual localhost UI.
- Research uses platform, industry, keyword, competitor URLs, and a selected sort. Never claim unavailable metrics are exact.
- Treat competitor videos as demand signals only. Produce an original angle and language.
- Generate exactly three script candidates unless the user provides a script. Let the user edit the candidate; only the explicitly approved text advances.
- Split production into HeyGen Avatar and No-face. Also support a source-video upload route.
- Never spend HeyGen credit without action-time confirmation.
- Create `EDIT_REQUEST.md` before editing. Store every feedback round and preserve prior renders.
- Publishing defaults to Skip. Require action-time confirmation for any real post or schedule.

