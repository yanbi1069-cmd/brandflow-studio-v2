"""Prepare and validate a BrandFlow production job.

This command is intentionally deterministic and does not spend API credits. It turns
the manifest downloaded from the web studio into a local job folder, validates the
contract, and prints the exact production sequence for the media tools in scripts/.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


REQUIRED_SCRIPT_FIELDS = ("hook", "body", "cta")
REQUIRED_QA_FIELDS = ("captionSafeArea", "requireNoFlashFrames", "requireVoiceAlignment")


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "video-project"


def validate_manifest(data: dict) -> list[str]:
    errors: list[str] = []
    project = data.get("project") or {}
    script = data.get("script") or {}
    production = data.get("production") or {}
    qa = data.get("qa") or {}

    if data.get("schemaVersion") != "1.0":
        errors.append("schemaVersion must be 1.0")
    if not project.get("brand"):
        errors.append("project.brand is required")
    if not project.get("niche"):
        errors.append("project.niche is required")
    for field in REQUIRED_SCRIPT_FIELDS:
        if not str(script.get(field, "")).strip():
            errors.append(f"script.{field} is required")
    if production.get("videoMode") not in {"avatar", "noface"}:
        errors.append("production.videoMode must be avatar or noface")
    if not (production.get("editStyle") or {}).get("id"):
        errors.append("production.editStyle.id is required")
    for field in REQUIRED_QA_FIELDS:
        if qa.get(field) is not True:
            errors.append(f"qa.{field} must be true")
    if int(project.get("targetDurationSec", 0)) > int(qa.get("maxDurationSec", 60)):
        errors.append("target duration exceeds QA maximum")
    return errors


def build_job(manifest_path: Path, output_root: Path) -> Path:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = validate_manifest(data)
    if errors:
        raise ValueError("Manifest invalid:\n- " + "\n- ".join(errors))

    project = data["project"]
    brand = project["brand"]
    brand_name = brand.get("name") if isinstance(brand, dict) else str(brand)
    job_slug = slugify(f"{datetime.now():%Y-%m-%d}-{brand_name}-{project['niche']}")
    job_dir = output_root / job_slug
    job_dir.mkdir(parents=True, exist_ok=False)

    shutil.copy2(manifest_path, job_dir / "manifest.json")
    script = data["script"]
    spoken = "\n\n".join(script[field].strip() for field in REQUIRED_SCRIPT_FIELDS)
    (job_dir / "voice_script_heygen.txt").write_text(spoken, encoding="utf-8")

    scenes = {
        "scenes": [
            {"label": "hook", "text": script["hook"].strip()},
            {"label": "body", "text": script["body"].strip()},
            {"label": "cta", "text": script["cta"].strip()},
        ]
    }
    (job_dir / "script_scenes.json").write_text(
        json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    phrases = [
        {"spoken": script[field].strip(), "display": script[field].strip()}
        for field in REQUIRED_SCRIPT_FIELDS
    ]
    (job_dir / "subtitle_phrases.json").write_text(
        json.dumps(phrases, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    checklist = """# Production checklist

- [ ] Confirm avatar and cloned voice belong to this brand.
- [ ] Generate or attach source video as `avatar.mp4`.
- [ ] Align captions; inspect every score below 0.85.
- [ ] Map each technical claim to a proof visual.
- [ ] Confirm adjacent B-roll slots do not expose flash frames.
- [ ] Render `final.mp4` and inspect the full video plus scene boundaries.
- [ ] Confirm duration is under 60 seconds and captions stay within two lines.
"""
    (job_dir / "QA_CHECKLIST.md").write_text(checklist, encoding="utf-8")
    return job_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a BrandFlow local production job")
    parser.add_argument("manifest", type=Path, help="JSON manifest downloaded from BrandFlow Studio")
    parser.add_argument("--output", type=Path, default=Path("workspace/jobs"), help="Job output root")
    parser.add_argument("--validate-only", action="store_true", help="Validate without creating files")
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

    job_dir = build_job(args.manifest, args.output)
    print(f"READY: {job_dir.resolve()}")
    print("NEXT: add avatar.mp4, then follow engine/PRODUCTION.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
