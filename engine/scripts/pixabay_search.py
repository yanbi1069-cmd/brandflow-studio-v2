"""
Pixabay stock video search + download for B-roll — nguồn dự phòng khi Pexels
(pexels_search.py) hết kết quả hoặc trả trùng clip ID đã dùng trước đó.

Cùng function names/behavior với pexels_search.py (search_portrait_video,
download_video) để 2 script hoán đổi cho nhau được trong skill personal-brand-video.

Lưu ý: khác Pexels, API video của Pixabay KHÔNG có tham số orientation - clip
portrait được lọc thủ công từ các size variant (large/medium/small/tiny) trả về
mỗi hit, vì phần lớn kho video của Pixabay là landscape nên kết quả portrait sẽ
ít hơn Pexels.

Setup: cần PIXABAY_API_KEY trong .env (lấy tại https://pixabay.com/api/docs/).
Kết quả gọi API phải được cache 24 giờ; stock_broll.py thực thi quy tắc này.

Usage: python pixabay_search.py <query> <output_path>
"""

import sys, os, requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env.local")
load_dotenv(Path(__file__).parent.parent / ".env", override=False)
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")


def search_portrait_asset(query: str, used_urls: set | None = None, api_key: str | None = None) -> dict | None:
    """Return a traceable portrait stock asset, or None when no match exists."""
    key = api_key or PIXABAY_API_KEY
    if not key:
        raise RuntimeError("Thiếu PIXABAY_API_KEY")
    resp = requests.get(
        "https://pixabay.com/api/videos/",
        params={"key": key, "q": query, "per_page": 20, "safesearch": "true", "order": "popular"},
        timeout=60
    )
    resp.raise_for_status()
    data = resp.json()

    for hit in data.get("hits", []):
        variants = [v for v in hit.get("videos", {}).values()
                    if (v.get("height") or 0) > (v.get("width") or 0)]
        variants.sort(key=lambda v: abs((v.get("width") or 720) - 720))
        for v in variants:
            url = v.get("url")
            if url and (not used_urls or url not in used_urls):
                user = hit.get("user") or ""
                user_id = hit.get("user_id") or ""
                return {"provider": "pixabay", "id": str(hit.get("id") or ""), "query": query, "download_url": url, "source_url": hit.get("pageURL") or "", "creator": user, "creator_url": f"https://pixabay.com/users/{user}-{user_id}/" if user and user_id else "", "width": v.get("width"), "height": v.get("height"), "duration": hit.get("duration"), "license": "Pixabay Content License", "license_url": "https://pixabay.com/service/license-summary/"}
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

    print(f"Searching Pixabay for: '{query}'...")
    url = search_portrait_video(query)
    if not url:
        print(f"  No portrait video found for '{query}'")
        sys.exit(1)

    print(f"  Found: {url[:80]}...")
    download_video(url, output_path)
