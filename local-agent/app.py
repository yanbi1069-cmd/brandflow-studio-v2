from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from agent_core import (
    DATA_DIR,
    JOBS,
    PROJECTS,
    ROOT,
    build_edit_plan,
    build_qa_report,
    check_claims,
    create_noface_plan,
    prepare_noface_source,
    demo_research,
    demo_scripts,
    get_domain_pack,
    get_edit_style,
    live_research,
    live_scripts,
    load_settings,
    now_iso,
    read_json,
    render_edit,
    run_publish,
    safe_filename,
    safe_settings_payload,
    save_secrets,
    save_settings,
    submit_heygen,
    write_json,
)


STATIC_DIR = ROOT / "static"
MAX_BODY = 1024 * 1024
MAX_UPLOAD = 1024 * 1024 * 1024
STUDIO_URL = os.getenv("BRANDFLOW_STUDIO_URL", "http://localhost:3000/multi-niche")


class AgentHandler(BaseHTTPRequestHandler):
    server_version = "BrandFlowMultiNicheAgent/2.0"

    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def _json(self, value, status=HTTPStatus.OK):
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _error(self, message, status=HTTPStatus.BAD_REQUEST):
        self._json({"ok": False, "error": str(message)}, status)

    def _body_json(self):
        if self.headers.get("X-BrandFlow-Agent") != "1" and self.headers.get("X-CFD-Agent") != "1":
            raise PermissionError("Thiếu local request header")
        content_type = self.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            raise ValueError("Content-Type phải là application/json")
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BODY:
            raise ValueError("Request quá lớn")
        return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path in {"", "/", "/workflow", "/multi-niche"}:
                return self._redirect_to_studio()
            if parsed.path == "/api/health":
                return self._json({"ok": True, "service": "personal-brand-video-agent", "version": 2, "finance_compatible": True})
            if parsed.path == "/api/settings":
                return self._json({"ok": True, "settings": safe_settings_payload()})
            if parsed.path == "/api/projects":
                return self._json({"ok": True, "projects": PROJECTS.list()})
            if parsed.path.startswith("/api/projects/"):
                project_id = parsed.path.rsplit("/", 1)[-1]
                project = PROJECTS.get(project_id)
                folder = PROJECTS.folder(project_id)
                artifacts = {
                    "script_candidates": read_json(folder / "script_candidates.json", []),
                    "approved_script": read_json(folder / "approved_script.json", None),
                    "noface_plan": read_json(folder / "noface_plan.json", None),
                    "edit_request": read_json(folder / "edit_request.json", None),
                    "edit_plan": read_json(folder / "edit_plan.json", None),
                    "edit_feedback": read_json(folder / "edit_feedback.json", []),
                    "qa_report": read_json(folder / "qa_report.json", None),
                    "publish": read_json(folder / "publish.json", None),
                    "skip": read_json(folder / "skip.json", None),
                    "media": [item.name for item in folder.glob("*.mp4") if item.is_file()],
                }
                return self._json({"ok": True, "project": project, "artifacts": artifacts})
            if parsed.path.startswith("/api/jobs/"):
                return self._json({"ok": True, "job": JOBS.get(parsed.path.rsplit("/", 1)[-1])})
            if parsed.path == "/api/media":
                return self._serve_media(parse_qs(parsed.query))
            return self._serve_static(parsed.path)
        except KeyError as exc:
            return self._error(exc.args[0], HTTPStatus.NOT_FOUND)
        except Exception as exc:
            return self._error(exc, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _redirect_to_studio(self):
        self.send_response(HTTPStatus.TEMPORARY_REDIRECT)
        self.send_header("Location", STUDIO_URL)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/upload":
                return self._upload()
            body = self._body_json()
            if parsed.path == "/api/settings":
                if body.get("secrets"):
                    save_secrets(body["secrets"])
                settings = save_settings(body.get("settings") or {})
                return self._json({"ok": True, "settings": settings})
            if parsed.path == "/api/research":
                mode = body.get("mode", "demo")
                if mode == "demo":
                    rows = demo_research(body.get("platforms") or ["youtube"], body.get("industry") or "cfd-finance", body.get("keyword") or "")
                    return self._json({"ok": True, "mode": "demo", "rows": rows})
                job = JOBS.start("research", lambda progress: live_research(body, progress))
                return self._json({"ok": True, "job": job}, HTTPStatus.ACCEPTED)
            if parsed.path == "/api/projects":
                selected = body.get("selected_video")
                domain = get_domain_pack(body.get("domain_id") or (selected or {}).get("industry") or "finance")
                style = get_edit_style(body.get("style_id"), domain)
                title = body.get("title") or (selected or {}).get("title") or "Personal Brand Video"
                metadata = {"domain_id": domain.get("id"), "domain_pack": domain, "style_id": style.get("id")}
                return self._json({"ok": True, "project": PROJECTS.create(title, selected, metadata)}, HTTPStatus.CREATED)
            if parsed.path == "/api/scripts/generate":
                project = PROJECTS.get(body["project_id"])
                video = body.get("selected_video") or project.get("selected_video") or {}
                brand = load_settings().get("brand", {})
                domain = project.get("domain_pack") or get_domain_pack(body.get("domain_id") or project.get("domain_id") or video.get("industry"))
                if body.get("mode", "demo") == "demo":
                    scripts = demo_scripts(video, brand, domain)
                    folder = PROJECTS.folder(project["id"])
                    write_json(folder / "script_candidates.json", scripts)
                    PROJECTS.update(project["id"], {"stage": "scripts_ready"})
                    return self._json({"ok": True, "scripts": scripts})
                def generate_and_save(progress):
                    scripts = live_scripts(video, brand, progress, domain)
                    folder = PROJECTS.folder(project["id"])
                    write_json(folder / "script_candidates.json", scripts)
                    PROJECTS.update(project["id"], {"stage": "scripts_ready"})
                    return scripts

                job = JOBS.start("scripts", generate_and_save)
                return self._json({"ok": True, "job": job}, HTTPStatus.ACCEPTED)
            if parsed.path == "/api/scripts/approve":
                folder = PROJECTS.folder(body["project_id"])
                text = str(body.get("text") or "").strip()
                if not text:
                    raise ValueError("Kịch bản không được để trống")
                approved = {"id": body.get("script_id"), "text": text, "approved_at": body.get("approved_at")}
                write_json(folder / "approved_script.json", approved)
                (folder / "voice_script_heygen.txt").write_text(text, encoding="utf-8")
                project = PROJECTS.get(body["project_id"])
                claim_check = check_claims(text, project.get("domain_pack") or project.get("domain_id"))
                PROJECTS.update(body["project_id"], {"stage": "script_approved", "claim_check": claim_check})
                return self._json({"ok": True, "approved": approved, "claim_check": claim_check})
            if parsed.path == "/api/heygen":
                if not body.get("confirmed"):
                    raise PermissionError("Cần xác nhận tiêu credit HeyGen")
                folder = PROJECTS.folder(body["project_id"])
                job = JOBS.start("heygen", lambda progress: submit_heygen(folder, body, progress))
                PROJECTS.update(body["project_id"], {"stage": "heygen_submitted", "route": "avatar"})
                return self._json({"ok": True, "job": job}, HTTPStatus.ACCEPTED)
            if parsed.path == "/api/noface":
                if body.get("voice_source") == "approved-audio" and not body.get("confirmed"):
                    raise PermissionError("Cần xác nhận sử dụng credit HeyGen để tạo audio")
                folder = PROJECTS.folder(body["project_id"])
                def prepare_and_save(progress):
                    result = prepare_noface_source(folder, body, progress)
                    PROJECTS.update(body["project_id"], {"stage": "noface_ready", "route": "no-face", "uploaded_source": result["file"]})
                    return result

                job = JOBS.start("noface", prepare_and_save)
                PROJECTS.update(body["project_id"], {"stage": "noface_preparing", "route": "no-face"})
                return self._json({"ok": True, "job": job}, HTTPStatus.ACCEPTED)
            if parsed.path == "/api/feedback":
                folder = PROJECTS.folder(body["project_id"])
                feedback_path = folder / "edit_feedback.json"
                entries = json.loads(feedback_path.read_text(encoding="utf-8")) if feedback_path.exists() else []
                entry = {"version": len(entries) + 2, "text": str(body.get("text") or "").strip(), "created_at": body.get("created_at")}
                if not entry["text"]:
                    raise ValueError("Feedback không được để trống")
                entries.append(entry)
                write_json(feedback_path, entries)
                PROJECTS.update(body["project_id"], {"stage": "edit_feedback", "versions": entries})
                return self._json({"ok": True, "feedback": entry, "versions": entries})
            if parsed.path == "/api/edit-request":
                project = PROJECTS.get(body["project_id"])
                folder = PROJECTS.folder(project["id"])
                route = project.get("route") or body.get("route") or "source-video"
                domain = project.get("domain_pack") or get_domain_pack(project.get("domain_id"))
                style = get_edit_style(body.get("style_id") or project.get("style_id"), domain)
                request = {
                    "schema_version": 2,
                    "created_at": now_iso(),
                    "project_id": project["id"],
                    "route": route,
                    "training_pack": str(body.get("training_pack") or "reference-packs/CFD-Finance-Agent-Reference-Pack/nhi-finance-editorial-training-pack"),
                    "source_file": body.get("source_file") or project.get("uploaded_source") or "heygen_source.mp4",
                    "domain_pack": domain,
                    "edit_style": style,
                    "feedback": str(body.get("feedback") or "").strip(),
                    "status": "ready_for_multi_style_edit",
                }
                write_json(folder / "edit_request.json", request)
                edit_plan = build_edit_plan(folder, {**body, "style_id": style.get("id")}, domain)
                markdown = (
                    "# Multi-style Personal Brand Edit Request\n\n"
                    f"- Project: `{project['id']}`\n"
                    f"- Route: `{route}`\n"
                    f"- Source: `{request['source_file']}`\n"
                    f"- Training pack: `{request['training_pack']}`\n\n"
                    f"- Domain: `{domain.get('name')}`\n"
                    f"- Edit style: `{style.get('name')}`\n\n"
                    "## Yêu cầu\n\n"
                    + (request["feedback"] or "Dựng theo edit_plan.json: visual bám lời, phụ đề dễ đọc, không flash frame, QA toàn bộ video.")
                    + "\n"
                )
                (folder / "EDIT_REQUEST.md").write_text(markdown, encoding="utf-8")
                project = PROJECTS.update(project["id"], {"stage": "edit_requested", "edit_request": "EDIT_REQUEST.md", "style_id": style.get("id")})
                return self._json({"ok": True, "request": request, "edit_plan": edit_plan, "project": project}, HTTPStatus.CREATED)
            if parsed.path == "/api/edit":
                project = PROJECTS.get(body["project_id"])
                folder = PROJECTS.folder(project["id"])
                domain = project.get("domain_pack") or get_domain_pack(project.get("domain_id"))
                source_file = body.get("source_file") or project.get("uploaded_source") or "heygen_source.mp4"
                request = {**body, "source_file": source_file}
                def render_and_save(progress):
                    result = render_edit(folder, request, progress, domain)
                    PROJECTS.update(project["id"], {"stage": "render_ready", "latest_render": result.get("file"), "render_version": result.get("version")})
                    return result

                job = JOBS.start("edit", render_and_save)
                PROJECTS.update(project["id"], {"stage": "editing", "style_id": body.get("style_id") or project.get("style_id")})
                return self._json({"ok": True, "job": job}, HTTPStatus.ACCEPTED)
            if parsed.path == "/api/qa":
                project = PROJECTS.get(body["project_id"])
                folder = PROJECTS.folder(project["id"])
                report = build_qa_report(folder, body, project.get("domain_pack") or project.get("domain_id"))
                stage = "final_approved" if report["approved"] else "qa_required"
                project = PROJECTS.update(project["id"], {"stage": stage, "final_approved": report["approved"]})
                return self._json({"ok": True, "report": report, "project": project})
            if parsed.path == "/api/publish":
                project_id = body["project_id"]
                if body.get("mode") == "skip":
                    folder = PROJECTS.folder(project_id)
                    write_json(folder / "skip.json", {"skipped_at": now_iso(), "reason": str(body.get("reason") or "User selected local export only"), "external_change": False})
                    project = PROJECTS.update(project_id, {"stage": "complete", "publish_mode": "skip"})
                    return self._json({"ok": True, "project": project})
                folder = PROJECTS.folder(project_id)
                job = JOBS.start("publish", lambda progress: run_publish(folder, body, progress))
                PROJECTS.update(project_id, {"stage": "publishing", "publish_mode": body.get("mode")})
                return self._json({"ok": True, "job": job}, HTTPStatus.ACCEPTED)
            return self._error("Endpoint không tồn tại", HTTPStatus.NOT_FOUND)
        except PermissionError as exc:
            return self._error(exc, HTTPStatus.FORBIDDEN)
        except KeyError as exc:
            return self._error(exc.args[0], HTTPStatus.NOT_FOUND)
        except Exception as exc:
            return self._error(exc)

    def _upload(self):
        if self.headers.get("X-BrandFlow-Agent") != "1" and self.headers.get("X-CFD-Agent") != "1":
            raise PermissionError("Thiếu local request header")
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_UPLOAD:
            raise ValueError("File trống hoặc vượt giới hạn 1 GB")
        project_id = self.headers.get("X-Project-ID", "")
        filename = safe_filename(unquote(self.headers.get("X-Filename", "upload.bin")))
        kind = re.sub(r"[^a-z-]", "", self.headers.get("X-Upload-Kind", "source")) or "source"
        folder = PROJECTS.folder(project_id) / "uploads"
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / f"{kind}-{filename}"
        remaining = length
        with output.open("wb") as handle:
            while remaining:
                chunk = self.rfile.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                handle.write(chunk)
                remaining -= len(chunk)
        stored_name = f"uploads/{output.name}"
        PROJECTS.update(project_id, {"stage": "source_uploaded", "uploaded_source": stored_name})
        return self._json({"ok": True, "file": stored_name, "size": output.stat().st_size}, HTTPStatus.CREATED)

    def _serve_static(self, url_path: str):
        relative = "index.html" if url_path in {"", "/"} else url_path.lstrip("/")
        target = (STATIC_DIR / relative).resolve()
        if STATIC_DIR not in target.parents and target != STATIC_DIR:
            return self._error("Đường dẫn không hợp lệ", HTTPStatus.FORBIDDEN)
        if not target.exists() or not target.is_file():
            target = STATIC_DIR / "index.html"
        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(data)

    def _serve_media(self, query):
        project_id = (query.get("project_id") or [""])[0]
        filename = safe_filename((query.get("file") or [""])[0])
        folder = PROJECTS.folder(project_id)
        candidates = [folder / filename, folder / "uploads" / filename]
        target = next((item for item in candidates if item.exists() and item.is_file()), None)
        if target is None:
            return self._error("Không tìm thấy file", HTTPStatus.NOT_FOUND)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(target.stat().st_size))
        self.send_header("Content-Disposition", f'inline; filename="{target.name}"')
        self.end_headers()
        with target.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                self.wfile.write(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description="Personal Brand Video Agent — multi-niche, Finance-compatible")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    allow_remote = os.getenv("BRANDFLOW_ALLOW_REMOTE") == "1" or os.getenv("CFD_AGENT_ALLOW_REMOTE") == "1"
    if args.host not in {"127.0.0.1", "localhost"} and not allow_remote:
        raise SystemExit("Từ chối bind ra mạng. Chỉ dùng 127.0.0.1 hoặc đặt BRANDFLOW_ALLOW_REMOTE=1.")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), AgentHandler)
    print(f"Personal Brand Video Agent: http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
