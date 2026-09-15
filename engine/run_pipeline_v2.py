"""Validate and prepare a BrandFlow multi-niche manifest without spending API credits."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

SCRIPT_FIELDS = ("hook", "body", "cta")
VIDEO_MODES = {"avatar", "noface", "upload"}


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower().strip())
    return cleaned.strip("-") or "video-project"


def validate_manifest(data: dict) -> list[str]:
    errors: list[str] = []
    project = data.get("project") or {}
    domain = data.get("domainPack") or {}
    content_format = data.get("contentFormat") or {}
    script = data.get("script") or {}
    production = data.get("production") or {}
    qa = data.get("qa") or {}
    approvals = data.get("approvals") or {}
    if data.get("schemaVersion") != "2.0":
        errors.append("schemaVersion must be 2.0")
    for field in ("brand", "niche", "domainPackId", "contentFormatId"):
        if not project.get(field):
            errors.append(f"project.{field} is required")
    if domain.get("id") != project.get("domainPackId"):
        errors.append("domainPack.id must match project.domainPackId")
    if content_format.get("id") != project.get("contentFormatId"):
        errors.append("contentFormat.id must match project.contentFormatId")
    for field in ("proofTypes", "compliance"):
        if not isinstance(domain.get(field), list) or not domain[field]:
            errors.append(f"domainPack.{field} must be a non-empty array")
    for field in SCRIPT_FIELDS:
        if not str(script.get(field, "")).strip():
            errors.append(f"script.{field} is required")
    if production.get("videoMode") not in VIDEO_MODES:
        errors.append("production.videoMode must be avatar, noface, or upload")
    if not (production.get("editStyle") or {}).get("id"):
        errors.append("production.editStyle.id is required")
    for field in ("captionSafeArea", "requireNoFlashFrames", "requireVoiceAlignment", "requireSourceTraceability", "requireFullWatch"):
        if qa.get(field) is not True:
            errors.append(f"qa.{field} must be true")
    if int(project.get("targetDurationSec", 0)) > int(qa.get("maxDurationSec", 60)):
        errors.append("target duration exceeds QA maximum")
    expected_approvals = {"researchApproved", "scriptApproved", "externalCostConfirmed", "finalApproved", "publishingConfirmed"}
    if not expected_approvals.issubset(approvals):
        errors.append("approval gate fields are incomplete")
    return errors


def build_job(manifest_path: Path, output_root: Path) -> Path:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = validate_manifest(data)
    if errors:
        raise ValueError("Manifest invalid:\n- " + "\n- ".join(errors))
    project = data["project"]
    brand = project["brand"]
    brand_name = brand.get("name", "brand") if isinstance(brand, dict) else str(brand)
    job_dir = output_root / slugify(f"{datetime.now():%Y-%m-%d}-{brand_name}-{project['niche']}")
    job_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(manifest_path, job_dir / "manifest.json")
    script = data["script"]
    spoken = "\n\n".join(str(script[field]).strip() for field in SCRIPT_FIELDS)
    source = data.get("source")
    if source:
        (job_dir / "selected_video.json").write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
    candidates = [
        {"id": "script-1", "angle": "Cảnh báo trực diện", "text": spoken, "analysis": {"hook": "Tạo tension", "body": "Một cơ chế", "visual": "Proof theo domain", "cta": "Theo brand"}},
        {"id": "script-2", "angle": "Phản trực giác", "text": spoken, "analysis": {"hook": "Đảo niềm tin", "body": "Giải thích điều kiện", "visual": "Proof theo domain", "cta": "Theo brand"}},
        {"id": "script-3", "angle": "Case study nhanh", "text": spoken, "analysis": {"hook": "Tình huống thật", "body": "Trước-sau", "visual": "Proof theo domain", "cta": "Theo brand"}},
    ]
    (job_dir / "script_candidates.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    if data["approvals"].get("scriptApproved"):
        approved = {**candidates[0], "approved": True, "approvedAt": datetime.now().isoformat(timespec="seconds")}
        (job_dir / "approved_script.json").write_text(json.dumps(approved, ensure_ascii=False, indent=2), encoding="utf-8")
        (job_dir / "voice_script_heygen.txt").write_text(spoken, encoding="utf-8")
    edit_request = {
        "schemaVersion": "2.0",
        "domainPackId": project["domainPackId"],
        "contentFormatId": project["contentFormatId"],
        "videoMode": data["production"]["videoMode"],
        "editStyle": data["production"]["editStyle"],
        "proofTypes": data["domainPack"]["proofTypes"],
        "compliance": data["domainPack"]["compliance"],
        "disclaimer": data["domainPack"].get("disclaimer", ""),
        "status": "awaiting-source-and-script-approval",
    }
    (job_dir / "edit_request.json").write_text(json.dumps(edit_request, ensure_ascii=False, indent=2), encoding="utf-8")
    (job_dir / "EDIT_REQUEST.md").write_text(
        "# Multi-style Personal Brand Edit Request\n\n"
        f"- Domain: `{project['domainPackId']}`\n"
        f"- Format: `{project['contentFormatId']}`\n"
        f"- Video mode: `{data['production']['videoMode']}`\n"
        f"- Edit style: `{data['production']['editStyle']['id']}`\n\n"
        "Use `edit_plan.json` as the beat-level source of truth. Keep captions safe, visual proof traceable, and create a new version after feedback.\n",
        encoding="utf-8",
    )
    segments = [str(script[field]).strip() for field in SCRIPT_FIELDS]
    duration = int(project.get("targetDurationSec", 55))
    beat_length = duration / len(segments)
    style = data["production"]["editStyle"]
    proof_types = data["domainPack"]["proofTypes"]
    beats = []
    for index, segment in enumerate(segments):
        beats.append({
            "id": f"beat-{index + 1}", "start": round(index * beat_length, 2), "end": round((index + 1) * beat_length, 2),
            "spokenMeaning": segment, "visualRole": "hook" if index == 0 else ("cta" if index == len(segments) - 1 else "proof"),
            "assetSource": proof_types[index % len(proof_types)], "captionTreatment": style.get("caption", "clean-two-line"),
            "textEffect": (style.get("textEffects") or ["fade-rise"])[0], "transition": (style.get("transitions") or ["clean-cut"])[0],
            "audioCue": "hook-hit" if index == 0 else "voice-first", "fallback": "Typography + owned asset with source note",
        })
    edit_plan = {"schemaVersion": "2.0", "version": 1, "style": style, "domainPackId": project["domainPackId"], "verification": {"audioIsTimelineSource": True, "rotateTransitionFlavors": True, "payoffHoldMinSec": 1, "requireDraftFrameInspection": True, "requireFinalSpotCheck": True}, "beats": beats, "status": "awaiting-source-and-script-approval"}
    (job_dir / "edit_plan.json").write_text(json.dumps(edit_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    (job_dir / "edit_feedback.json").write_text("[]\n", encoding="utf-8")
    video_mode = data["production"]["videoMode"]
    if video_mode == "avatar":
        (job_dir / "heygen_request.json").write_text(json.dumps({"status": "awaiting-current-cost-confirmation", "scenes": segments, "externalCostConfirmed": data["approvals"].get("externalCostConfirmed", False)}, ensure_ascii=False, indent=2), encoding="utf-8")
    elif video_mode == "noface":
        (job_dir / "noface_plan.json").write_text(json.dumps({"route": "no-face", "scenes": segments, "proofTypes": proof_types, "style": style}, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        (job_dir / "upload_manifest.json").write_text(json.dumps({"route": "upload", "status": "awaiting-source-file"}, ensure_ascii=False, indent=2), encoding="utf-8")
    qa_checks = {"fullWatch": False, "captionSafeArea": False, "voiceAlignment": False, "noFlashFrames": False, "sourceTraceability": False, "claimsChecked": False}
    (job_dir / "qa_report.json").write_text(json.dumps({"checks": qa_checks, "approved": False}, ensure_ascii=False, indent=2), encoding="utf-8")
    distribution = data.get("distribution") or {"defaultAction": "skip"}
    distribution_name = "skip.json" if distribution.get("defaultAction", "skip") == "skip" else "publish.json"
    (job_dir / distribution_name).write_text(json.dumps({**distribution, "externalActionExecuted": False, "publishingConfirmed": data["approvals"].get("publishingConfirmed", False)}, ensure_ascii=False, indent=2), encoding="utf-8")
    (job_dir / "APPROVALS.json").write_text(json.dumps(data["approvals"], ensure_ascii=False, indent=2), encoding="utf-8")
    return job_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a BrandFlow v2 multi-niche job")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, default=Path("workspace/jobs"))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate_manifest(data)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    if args.validate_only:
        print("VALID")
        return 0
    print(f"READY: {build_job(args.manifest, args.output).resolve()}")
    print("NEXT: approve script, attach source media, then use the multi-style-video-editor skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
