"""Prepare contextual B-roll with traceable Pexels -> Pixabay fallback.

Context beats are sent to stock providers. Proof and metaphor beats use local
motion graphics. No-face plans require a visual slot for every voice beat.
Pixabay selections are cached for at least 24 hours as required by its API.
No API key is ever written to a manifest or cache file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

import pexels_search
import pixabay_search
import technical_broll

PROVIDERS = {"pexels": pexels_search, "pixabay": pixabay_search}
KEY_NAMES = {"pexels": "PEXELS_API_KEY", "pixabay": "PIXABAY_API_KEY"}
CACHE_TTL_SECONDS = 24 * 60 * 60


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_query(value: str) -> str:
    value = re.sub(r"\s+", " ", re.sub(r"[^\w\s%-]", " ", value, flags=re.UNICODE)).strip()
    return value[:100] or "business lifestyle"


def normalized_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value).lower().replace("đ", "d"))
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def semantic_stock_query(beat: dict[str, Any], domain_id: str = "") -> tuple[str, str]:
    """Translate narration meaning into a concrete stock-search intent.

    Stock APIs perform much better with concise English visual objects/actions
    than with a full Vietnamese claim or conclusion.
    """
    spoken = str(beat.get("spokenMeaning") or beat.get("spoken_meaning") or "")
    explicit = str(beat.get("assetQuery") or beat.get("asset_query") or "").strip()
    normalized = normalized_text(explicit or spoken)
    mappings = [
        (("video hoat hinh", "ai video", "tao sinh"), "video editor computer", "ai-creative-context"),
        (("gpu", "chi phi van hanh", "du lieu dao tao"), "data center servers", "data-center-context"),
        (("startup", "huy dong", "quy sequoia"), "startup investor meeting", "startup-investment-context"),
        (("90 nha dau tu", "nha dau tu ai", "thua lo"), "worried investor reviewing losses on laptop", "investor-loss-context"),
        (("5 danh muc", "10 danh muc", "phan bo", "etf"), "planning investment portfolio", "portfolio-planning-context"),
        (("bao cao tai chinh", "hang quy", "pitchbook"), "analyst reading financial report on computer", "financial-report-context"),
        (("theo doi", "tin tai chinh"), "person following financial news on smartphone", "finance-news-context"),
        (("mot cong ty", "duy nhat", "bai hoc"), "diversified investment portfolio", "diversification-context"),
        (("giao duc", "khuyen nghi dau tu"), "person learning personal finance", "education-disclaimer-context"),
        (("ly nuoc", "mep ban", "day ly", "cham mep"), "hand pushing glass of water near table edge close up", "physical-metaphor"),
        (("khach hang", "tu van"), "business consultant meeting client office", "client-context"),
        (("hoc vien", "dao tao", "lop hoc"), "adult students learning in modern classroom", "education-context"),
        (("bac si", "benh nhan", "suc khoe"), "doctor consulting patient in clinic", "health-context"),
        (("san pham", "dong goi"), "small business product packaging close up", "product-context"),
        (("dien thoai", "mang xa hoi"), "person scrolling social media on smartphone close up", "social-context"),
        (("may tinh", "lam viec", "quy trinh"), "professional working on computer at desk close up", "work-context"),
    ]
    for triggers, query, intent in mappings:
        if any(trigger in normalized for trigger in triggers):
            return query, intent
    return "", "no-concrete-visual"


def cache_path(cache_dir: Path, provider: str, query: str) -> Path:
    digest = hashlib.sha256(f"{provider}:{query.lower()}".encode("utf-8")).hexdigest()[:20]
    return cache_dir / f"{provider}-{digest}.json"


def cached_asset(cache_dir: Path, provider: str, query: str, used_urls: set[str]) -> dict | None:
    path = cache_path(cache_dir, provider, query)
    if not path.is_file() or time.time() - path.stat().st_mtime > CACHE_TTL_SECONDS:
        return None
    asset = read_json(path)
    identity = f"{asset.get('provider')}:{asset.get('id')}"
    return asset if asset.get("download_url") not in used_urls and identity not in used_urls else None


def select_asset(query: str, cache_dir: Path, used_urls: set[str], providers: list[str] | None = None) -> tuple[dict | None, list[dict]]:
    attempts: list[dict] = []
    for provider in providers or ["pexels", "pixabay"]:
        if provider not in PROVIDERS:
            attempts.append({"provider": provider, "status": "unsupported"})
            continue
        cached = cached_asset(cache_dir, provider, query, used_urls)
        if cached:
            return {**cached, "cache_hit": True}, attempts + [{"provider": provider, "status": "cache-hit"}]
        api_key = os.getenv(KEY_NAMES[provider])
        if not api_key:
            attempts.append({"provider": provider, "status": "missing-key"})
            continue
        try:
            asset = PROVIDERS[provider].search_portrait_asset(query, used_urls, api_key=api_key)
        except Exception as error:
            attempts.append({"provider": provider, "status": "error", "message": str(error)[:240]})
            continue
        if not asset:
            attempts.append({"provider": provider, "status": "no-match"})
            continue
        cache_dir.mkdir(parents=True, exist_ok=True)
        write_json(cache_path(cache_dir, provider, query), asset)
        return {**asset, "cache_hit": False}, attempts + [{"provider": provider, "status": "selected"}]
    return None, attempts


def close_noface_gaps(slots: list[dict], duration: float) -> list[dict]:
    """Extend adjacent visuals to a shared boundary so no-face never shows a blank frame."""
    ordered = sorted(slots, key=lambda item: (float(item["start"]), float(item["end"])))
    if not ordered:
        return ordered
    ordered[0]["start"] = 0.0
    for previous, current in zip(ordered, ordered[1:]):
        boundary = round((float(previous["end"]) + float(current["start"])) / 2, 3)
        previous["end"] = boundary
        current["start"] = boundary
    ordered[-1]["end"] = round(duration, 3)
    return ordered


def prepare_context_broll(edit_plan_path: Path, media_dir: Path, slots_path: Path, manifest_path: Path, dry_run: bool = False) -> dict:
    plan = read_json(edit_plan_path)
    cache_dir = media_dir.parent / ".stock-cache"
    used_urls: set[str] = set()
    slots: list[dict] = []
    assets: list[dict] = []
    fallbacks: list[dict] = []
    palette = (plan.get("style") or {}).get("palette") or []
    style_id = str((plan.get("style") or {}).get("id") or "editorial-proof")
    domain_id = str(plan.get("domain_pack_id") or "")
    noface = str(plan.get("video_mode") or "") == "noface"
    beats_by_id = {str(beat.get("id")): beat for beat in plan.get("beats", [])}
    for beat in plan.get("beats", []):
        role = beat.get("visualRole") or beat.get("visual_role")
        name = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(beat.get("id") or f"beat-{len(slots)+1}"))
        start, end = float(beat.get("start", 0)), float(beat.get("end", 0))
        if role in {"proof", "metaphor"}:
            if dry_run:
                fallbacks.append({"beat_id": beat.get("id"), "status": "planned-technical-motion", "start": start, "end": end})
                continue
            output = media_dir / "chartanimator" / f"{name}.mp4"
            try:
                technical = technical_broll.render_technical_clip(beat, output, palette, style_id)
            except Exception as error:
                fallbacks.append({"beat_id": beat.get("id"), "status": "technical-render-error-use-presenter", "message": str(error)[:240]})
                continue
            slots.append({"name": name, "type": "chart", "start": start, "end": end, "visual_role": role})
            assets.append({
                "provider": "brandflow-local",
                "file": str(output.relative_to(media_dir.parent)).replace("\\", "/"),
                "usage": "technical-proof",
                "beat_id": beat.get("id"),
                "start": start,
                "end": end,
                **technical,
            })
            continue
        if role != "context":
            if noface:
                role = "context"
            else:
                continue
        query, intent = semantic_stock_query(beat, domain_id)
        if intent == "physical-metaphor":
            if dry_run:
                fallbacks.append({"beat_id": beat.get("id"), "status": "planned-local-metaphor", "intent": intent})
                continue
            if slots and assets and assets[-1].get("kind") == "glass-metaphor" and start - slots[-1]["end"] <= 0.75:
                previous = assets[-1]
                carrier = beats_by_id.get(str(previous.get("beat_id"))) or beat
                extended = {**carrier, "start": slots[-1]["start"], "end": end}
                source = media_dir.parent / str(previous["file"])
                try:
                    technical = technical_broll.render_technical_clip(extended, source, palette, style_id)
                except Exception as error:
                    fallbacks.append({"beat_id": beat.get("id"), "status": "metaphor-extend-error-use-presenter", "message": str(error)[:240]})
                    continue
                slots[-1]["end"] = end
                previous["end"] = end
                previous["duration"] = technical["duration"]
                previous.setdefault("voice_beat_ids", [previous["beat_id"]]).append(beat.get("id"))
                continue
            output = media_dir / "chartanimator" / f"{name}.mp4"
            try:
                technical = technical_broll.render_technical_clip(beat, output, palette, style_id)
            except Exception as error:
                fallbacks.append({"beat_id": beat.get("id"), "status": "metaphor-render-error-use-presenter", "message": str(error)[:240]})
                continue
            slots.append({"name": name, "type": "chart", "start": start, "end": end, "visual_role": "context"})
            assets.append({
                "provider": "brandflow-local",
                "file": str(output.relative_to(media_dir.parent)).replace("\\", "/"),
                "usage": "voice-matched-metaphor",
                "intent": intent,
                "beat_id": beat.get("id"),
                "start": start,
                "end": end,
                **technical,
            })
            continue
        if not query:
            if not noface:
                fallbacks.append({"beat_id": beat.get("id"), "status": "no-concrete-visual-use-presenter", "spoken_meaning": str(beat.get("spoken_meaning") or "")[:140]})
                continue
            output = media_dir / "chartanimator" / f"{name}.mp4"
            if dry_run:
                fallbacks.append({"beat_id": beat.get("id"), "status": "planned-local-noface-fallback"})
                continue
            technical = technical_broll.render_technical_clip(beat, output, palette, style_id)
            slots.append({"name": name, "type": "chart", "start": start, "end": end, "visual_role": "context"})
            assets.append({"provider": "brandflow-local", "file": str(output.relative_to(media_dir.parent)).replace("\\", "/"), "usage": "noface-coverage-fallback", "beat_id": beat.get("id"), "start": start, "end": end, **technical})
            continue
        query = safe_query(query)
        providers = beat.get("stockProviders") or beat.get("stock_providers") or ["pexels", "pixabay"]
        if dry_run:
            fallbacks.append({"beat_id": beat.get("id"), "query": query, "intent": intent, "status": "planned-stock", "provider_order": providers})
            continue
        asset, attempts = select_asset(query, cache_dir, used_urls, providers)
        if not asset:
            if not noface:
                fallbacks.append({"beat_id": beat.get("id"), "query": query, "status": "use-presenter-or-typography", "attempts": attempts})
                continue
            output = media_dir / "chartanimator" / f"{name}.mp4"
            technical = technical_broll.render_technical_clip(beat, output, palette, style_id)
            slots.append({"name": name, "type": "chart", "start": start, "end": end, "visual_role": "context"})
            assets.append({"provider": "brandflow-local", "file": str(output.relative_to(media_dir.parent)).replace("\\", "/"), "usage": "noface-stock-fallback", "query": query, "attempts": attempts, "beat_id": beat.get("id"), "start": start, "end": end, **technical})
            continue
        provider = asset["provider"]
        output = media_dir / provider / f"{name}.mp4"
        PROVIDERS[provider].download_video(asset["download_url"], str(output))
        used_urls.add(asset["download_url"])
        used_urls.add(f"{provider}:{asset.get('id')}")
        slots.append({"name": name, "type": provider, "start": start, "end": end, "visual_role": role})
        assets.append({**{k: v for k, v in asset.items() if k != "download_url"}, "query": query, "intent": intent, "file": str(output.relative_to(media_dir.parent)).replace("\\", "/"), "usage": "context-broll", "beat_id": beat.get("id"), "start": start, "end": end, "attempts": attempts})
    if noface:
        slots = close_noface_gaps(slots, float(plan.get("duration_seconds") or 0))
    write_json(slots_path, {"slots": slots})
    coverage = sum(max(0.0, float(slot["end"]) - float(slot["start"])) for slot in slots)
    manifest = {"schema_version": 2, "provider_order": ["brandflow-local-technical", "owned-assets", "pexels", "pixabay", "local-noface-fallback"], "stock_is_context_only": True, "technical_proof_is_generated": True, "full_visual_coverage_required": noface, "covered_seconds": round(coverage, 3), "assets": assets, "fallbacks": fallbacks}
    write_json(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare contextual stock B-roll from an edit plan")
    parser.add_argument("edit_plan", type=Path)
    parser.add_argument("--media-dir", type=Path, required=True)
    parser.add_argument("--slots", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    manifest = prepare_context_broll(args.edit_plan, args.media_dir, args.slots, args.manifest, args.dry_run)
    print(f"READY: {len(manifest['assets'])} stock clip(s); {len(manifest['fallbacks'])} fallback beat(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
