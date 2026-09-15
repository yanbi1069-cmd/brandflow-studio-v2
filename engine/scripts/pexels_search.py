"""
Pexels stock video search + download for B-roll (non-chart segments)
Ported from: D:\\Agent - Skill\\Agent video thương hiệu cá nhân (gốc)\\app\\utils\\pexels.py

Usage: python pexels_search.py <query> <output_path>
"""

import sys, os, requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env.local")
load_dotenv(Path(__file__).parent.parent / ".env", override=False)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")


def search_portrait_asset(query: str, used_urls: set | None = None, api_key: str | None = None) -> dict | None:
    """Return a traceable portrait stock asset, or None when no match exists."""
    key = api_key or PEXELS_API_KEY
    if not key:
        raise RuntimeError("Thiếu PEXELS_API_KEY")
    resp = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": key},
        params={"query": query, "per_page": 10, "orientation": "portrait"},
        timeout=60
    )
    resp.raise_for_status()
    data = resp.json()

    for video in data.get("videos", []):
        files = [f for f in video.get("video_files", []) if (f.get("height") or 0) > (f.get("width") or 0) and (f.get("width") or 0) >= 480]
        if not files:
            files = [f for f in video.get("video_files", []) if (f.get("height") or 0) > (f.get("width") or 0)]
        files.sort(key=lambda f: abs((f.get("width") or 720) - 720))
        for f in files:
            url = f.get("link")
            if url and (not used_urls or url not in used_urls):
                user = video.get("user") or {}
                return {"provider": "pexels", "id": str(video.get("id") or ""), "query": query, "download_url": url, "source_url": video.get("url") or "", "creator": user.get("name") or "", "creator_url": user.get("url") or "", "width": f.get("width"), "height": f.get("height"), "duration": video.get("duration"), "license": "Pexels License", "license_url": "https://www.pexels.com/license/"}
    return None


def search_portrait_video(query: str, used_urls: set | None = None) -> str | None:
    """Backward-compatible direct URL helper."""
    asset = search_portrait_asset(query, used_urls)
    return asset["download_url"] if asset else None


def download_video(url: str, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"  Downloaded: {output_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    query = sys.argv[1]
    output_path = sys.argv[2]

    print(f"Searching Pexels for: '{query}'...")
    url = search_portrait_video(query)
    if not url:
        print(f"  No video found for '{query}'")
        sys.exit(1)

    print(f"  Found: {url[:80]}...")
    download_video(url, output_path)
