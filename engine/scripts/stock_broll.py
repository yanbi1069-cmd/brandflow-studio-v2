"""Prepare contextual B-roll with traceable Pexels -> Pixabay fallback.

Only beats marked ``context`` are sent to stock providers. Proof, metaphor,
presenter, hook and CTA beats remain owned/designed/source-video visuals.
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
from pathlib import Path
from typing import Any

import pexels_search
import pixabay_search

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


def cache_path(cache_dir: Path, provider: str, query: str) -> Path:
    digest = hashlib.sha256(f"{provider}:{query.lower()}".encode("utf-8")).hexdigest()[:20]
    return cache_dir / f"{provider}-{digest}.json"


def cached_asset(cache_dir: Path, provider: str, query: str, used_urls: set[str]) -> dict | None:
    path = cache_path(cache_dir, provider, query)
    if not path.is_file() or time.time() - path.stat().st_mtime > CACHE_TTL_SECONDS:
        return None
    asset = read_json(path)
    return asset if asset.get("download_url") not in used_urls else None


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


def prepare_context_broll(edit_plan_path: Path, media_dir: Path, slots_path: Path, manifest_path: Path, dry_run: bool = False) -> dict:
    plan = read_json(edit_plan_path)
    cache_dir = media_dir.parent / ".stock-cache"
    used_urls: set[str] = set()
    slots: list[dict] = []
    assets: list[dict] = []
    fallbacks: list[dict] = []
    for beat in plan.get("beats", []):
        role = beat.get("visualRole") or beat.get("visual_role")
        if role != "context":
            continue
        name = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(beat.get("id") or f"context-{len(slots)+1}"))
        query = safe_query(str(beat.get("assetQuery") or beat.get("asset_query") or beat.get("spokenMeaning") or beat.get("spoken_meaning") or ""))
        providers = beat.get("stockProviders") or beat.get("stock_providers") or ["pexels", "pixabay"]
        if dry_run:
            fallbacks.append({"beat_id": beat.get("id"), "query": query, "status": "planned", "provider_order": providers})
            continue
        asset, attempts = select_asset(query, cache_dir, used_urls, providers)
        if not asset:
            fallbacks.append({"beat_id": beat.get("id"), "query": query, "status": "use-presenter-or-typography", "attempts": attempts})
            continue
        provider = asset["provider"]
        output = media_dir / provider / f"{name}.mp4"
        PROVIDERS[provider].download_video(asset["download_url"], str(output))
        used_urls.add(asset["download_url"])
        start, end = float(beat.get("start", 0)), float(beat.get("end", 0))
        slots.append({"name": name, "type": provider, "start": start, "end": end})
        assets.append({**{k: v for k, v in asset.items() if k != "download_url"}, "file": str(output.relative_to(media_dir.parent)).replace("\\", "/"), "usage": "context-broll", "beat_id": beat.get("id"), "start": start, "end": end, "attempts": attempts})
    write_json(slots_path, {"slots": slots})
    manifest = {"schema_version": 1, "provider_order": ["owned-assets", "pexels", "pixabay", "presenter-or-typography"], "stock_is_context_only": True, "assets": assets, "fallbacks": fallbacks}
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
