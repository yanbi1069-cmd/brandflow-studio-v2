from __future__ import annotations

import json
import hashlib
import os
import re
import statistics
import subprocess
import threading
import time
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import requests
from dotenv import dotenv_values, load_dotenv


ROOT = Path(__file__).resolve().parent
DEFAULTS_PATH = ROOT / "config" / "defaults.json"
DOMAIN_PACKS_PATH = ROOT.parent / "config" / "domain-packs.json"
EDIT_STYLES_PATH = ROOT.parent / "config" / "edit-styles-v2.json"
ENV_PATH = ROOT / ".env"
PROJECT_ENV_PATH = ROOT.parent / ".env.local"
DATA_DIR = Path(os.getenv("BRANDFLOW_DATA_DIR") or ROOT / "data").resolve()
WORKSPACE = Path(os.getenv("BRANDFLOW_WORKSPACE") or os.getenv("CFD_AGENT_WORKSPACE") or ROOT / "workspace").resolve()
PROJECT_ROOT = Path(os.getenv("BRANDFLOW_PROJECT_ROOT") or os.getenv("CFD_AGENT_PROJECT_ROOT") or ROOT.parents[1]).resolve()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-") or "video"


def safe_filename(value: str) -> str:
    name = Path(value).name
    return re.sub(r"[^A-Za-z0-9._ -]+", "_", name)[:150] or "upload.bin"


def load_domain_packs() -> list[dict[str, Any]]:
    return read_json(DOMAIN_PACKS_PATH, []) or []


def load_edit_styles() -> list[dict[str, Any]]:
    return read_json(EDIT_STYLES_PATH, []) or []


def get_domain_pack(domain_id: str | None) -> dict[str, Any]:
    packs = load_domain_packs()
    requested = str(domain_id or "finance")
    if requested in {"cfd-finance", "forex", "gold", "gold-xauusd", "stocks", "crypto", "risk", "risk-management"}:
        requested = "finance"
    return next((item for item in packs if item.get("id") == requested), packs[0] if packs else {"id": requested, "name": requested, "proofTypes": [], "compliance": [], "disclaimer": ""})


def get_edit_style(style_id: str | None, domain: dict[str, Any] | None = None) -> dict[str, Any]:
    styles = load_edit_styles()
    requested = str(style_id or (domain or {}).get("defaultStyle") or "editorial-proof")
    return next((item for item in styles if item.get("id") == requested), styles[0] if styles else {"id": requested, "name": requested})


def load_settings() -> dict[str, Any]:
    defaults = read_json(DEFAULTS_PATH, {})
    local = read_json(DATA_DIR / "settings.json", {})
    merged = json.loads(json.dumps(defaults))
    for section, values in local.items():
        if isinstance(values, dict) and isinstance(merged.get(section), dict):
            merged[section].update(values)
        else:
            merged[section] = values
    return merged


def save_settings(patch: dict[str, Any]) -> dict[str, Any]:
    allowed = {"brand", "video", "research", "publishing", "integration"}
    current = read_json(DATA_DIR / "settings.json", {}) or {}
    for section, values in patch.items():
        if section not in allowed or not isinstance(values, dict):
            continue
        current.setdefault(section, {}).update(values)
    write_json(DATA_DIR / "settings.json", current)
    return load_settings()


def load_secrets() -> dict[str, str]:
    load_dotenv(PROJECT_ENV_PATH, override=False)
    load_dotenv(ENV_PATH, override=False)
    values = {k: str(v or "") for k, v in dotenv_values(PROJECT_ENV_PATH).items()}
    values.update({k: str(v or "") for k, v in dotenv_values(ENV_PATH).items()})
    for key in ("APIFY_API_TOKEN", "HEYGEN_API_KEY", "PEXELS_API_KEY", "PIXABAY_API_KEY", "KYMA_API_KEY", "KYMA_RESEARCH_MODEL", "KYMA_RERANK_MODEL", "KYMA_SCRIPT_MODEL", "KYMA_FALLBACK_MODEL", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        values[key] = os.getenv(key, values.get(key, ""))
    return values


def save_secrets(values: dict[str, Any]) -> None:
    allowed = {"APIFY_API_TOKEN", "HEYGEN_API_KEY", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"}
    current = {k: str(v or "") for k, v in dotenv_values(ENV_PATH).items()} if ENV_PATH.exists() else {}
    for key, value in values.items():
        if key in allowed and value is not None and str(value) != "••••••••••••••":
            current[key] = str(value).replace("\r", "").replace("\n", "")
    ENV_PATH.write_text("\n".join(f"{key}={value}" for key, value in current.items()) + "\n", encoding="utf-8")


def safe_settings_payload() -> dict[str, Any]:
    settings = load_settings()
    secrets = load_secrets()
    settings["connections"] = {
        "apify": bool(secrets.get("APIFY_API_TOKEN")),
        "heygen": bool(secrets.get("HEYGEN_API_KEY")),
        "pexels": bool(secrets.get("PEXELS_API_KEY")),
        "pixabay": bool(secrets.get("PIXABAY_API_KEY")),
        "llm": bool(secrets.get("KYMA_API_KEY") or secrets.get("LLM_API_KEY")),
    }
    return settings


class ProjectStore:
    def __init__(self, workspace: Path = WORKSPACE):
        self.workspace = workspace
        self.index_path = DATA_DIR / "projects.json"
        self.lock = threading.Lock()

    def _index(self) -> list[dict[str, Any]]:
        return read_json(self.index_path, []) or []

    def list(self) -> list[dict[str, Any]]:
        return sorted(self._index(), key=lambda item: item.get("updated_at", ""), reverse=True)

    def get(self, project_id: str) -> dict[str, Any]:
        for item in self._index():
            if item["id"] == project_id:
                return item
        raise KeyError("Không tìm thấy dự án")

    def folder(self, project_id: str) -> Path:
        item = self.get(project_id)
        folder = (self.workspace / item["relative_dir"]).resolve()
        if self.workspace not in folder.parents:
            raise ValueError("Đường dẫn dự án không hợp lệ")
        return folder

    def create(self, title: str, selected_video: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        created = datetime.now().astimezone()
        project_id = uuid.uuid4().hex[:12]
        relative = Path("content") / created.strftime("%Y-%m-%d") / f"{slugify(title)}-{project_id[:4]}"
        folder = self.workspace / relative
        folder.mkdir(parents=True, exist_ok=False)
        item = {
            "id": project_id,
            "title": title,
            "relative_dir": relative.as_posix(),
            "stage": "research_selected" if selected_video else "created",
            "selected_video": selected_video,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "versions": [],
            "publish_mode": "skip",
            **(metadata or {}),
        }
        write_json(folder / "pipeline.json", item)
        if selected_video:
            write_json(folder / "selected_video.json", selected_video)
        with self.lock:
            index = self._index()
            index.append(item)
            write_json(self.index_path, index)
        return item

    def update(self, project_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            index = self._index()
            found = None
            for item in index:
                if item["id"] == project_id:
                    item.update(patch)
                    item["updated_at"] = now_iso()
                    found = item
                    break
            if found is None:
                raise KeyError("Không tìm thấy dự án")
            write_json(self.index_path, index)
            write_json(self.folder(project_id) / "pipeline.json", found)
            return found


class JobManager:
    def __init__(self):
        self.jobs: dict[str, dict[str, Any]] = read_json(DATA_DIR / "jobs.json", {}) or {}
        for job in self.jobs.values():
            if job.get("status") in {"queued", "running"}:
                job["status"] = "interrupted"
                job["message"] = "Ứng dụng đã khởi động lại; có thể resume từ artifact đã lưu."
        self.lock = threading.Lock()
        self._persist()

    def _persist(self) -> None:
        write_json(DATA_DIR / "jobs.json", self.jobs)

    def start(self, kind: str, work: Callable[[Callable[[int, str], None]], Any]) -> dict[str, Any]:
        job_id = uuid.uuid4().hex[:12]
        job = {"id": job_id, "kind": kind, "status": "queued", "progress": 0, "message": "Đang xếp hàng", "created_at": now_iso()}
        with self.lock:
            self.jobs[job_id] = job
            self._persist()

        def runner() -> None:
            def progress(value: int, message: str) -> None:
                with self.lock:
                    job.update(progress=max(0, min(100, int(value))), message=message, updated_at=now_iso())
                    self._persist()
            try:
                with self.lock:
                    job.update(status="running", message="Đang chạy", updated_at=now_iso())
                    self._persist()
                result = work(progress)
                with self.lock:
                    job.update(status="done", progress=100, message="Hoàn thành", result=result, updated_at=now_iso())
                    self._persist()
            except Exception as exc:
                with self.lock:
                    job.update(status="error", message=str(exc), error=type(exc).__name__, updated_at=now_iso())
                    self._persist()

        threading.Thread(target=runner, daemon=True, name=f"brandflow-agent-{job_id}").start()
        return job

    def get(self, job_id: str) -> dict[str, Any]:
        if job_id not in self.jobs:
            raise KeyError("Không tìm thấy job")
        return self.jobs[job_id]


def platform_from_url(url: str) -> str:
    lowered = url.lower()
    if "youtube.com" in lowered or "youtu.be" in lowered:
        return "youtube"
    if "tiktok.com" in lowered:
        return "tiktok"
    if "facebook.com" in lowered or "fb.watch" in lowered:
        return "facebook"
    return "unknown"


def metric_number(item: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = item.get(key)
        if isinstance(value, (int, float)):
            return max(0, int(value))
    return 0


def compact_number(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def viral_reason(row: dict[str, Any]) -> str:
    reasons = []
    title = row["title"].lower()
    if any(token in title for token in ("why", "vì sao", "sai lầm", "đừng", "how", "cách")):
        reasons.append("hook tạo tò mò hoặc nêu pain point rõ")
    if row["engagement_pct"] >= 5:
        reasons.append("tỷ lệ tương tác cao")
    if row["comments"] >= 500:
        reasons.append("chủ đề kích thích thảo luận")
    if row["shares"] >= 1000:
        reasons.append("giá trị lưu/chia sẻ tốt")
    if not reasons:
        reasons.append("hiệu suất cao hơn mặt bằng của nhóm video được quét")
    return ", ".join(reasons).capitalize() + "."


def normalize_research_rows(items: list[dict[str, Any]], industry: str, keyword: str) -> list[dict[str, Any]]:
    rows = []
    for item in items:
        views = metric_number(item, "view_count", "views", "play_count")
        likes = metric_number(item, "like_count", "likes", "digg_count")
        comments = metric_number(item, "comment_count", "comments")
        shares = metric_number(item, "repost_count", "share_count", "shares")
        title = str(item.get("title") or item.get("description") or "Video không có tiêu đề").strip()
        url = str(item.get("webpage_url") or item.get("url") or "")
        platform = platform_from_url(url) if url else str(item.get("platform") or "unknown")
        engagement = round((likes + comments + shares) / views * 100, 2) if views else 0.0
        row = {
            "platform": platform,
            "channel": str(item.get("channel") or item.get("uploader") or item.get("uploader_id") or item.get("channel_id") or "Không rõ kênh"),
            "industry": industry,
            "industry_label": industry.replace("-", " ").title(),
            "title": title[:180],
            "url": url,
            "views": views,
            "views_text": compact_number(views),
            "likes": likes,
            "likes_text": compact_number(likes),
            "comments": comments,
            "comments_text": compact_number(comments),
            "shares": shares,
            "shares_text": compact_number(shares),
            "engagement_pct": engagement,
            "timestamp": item.get("timestamp") or item.get("release_timestamp"),
            "thumbnail": item.get("thumbnail") or "",
        }
        haystack = f"{title} {item.get('description', '')}".lower()
        if keyword and keyword.lower() not in haystack:
            continue
        rows.append(row)
    view_values = [row["views"] for row in rows if row["views"] > 0]
    median_views = statistics.median(view_values) if view_values else 1
    for row in rows:
        relative = row["views"] / max(1, median_views)
        row["viral_score"] = min(100, round(45 + min(relative, 4) * 10 + min(row["engagement_pct"], 10) * 1.5))
        row["viral_reason"] = viral_reason(row)
    return sorted(rows, key=lambda row: (row["viral_score"], row["views"]), reverse=True)


def demo_research(platforms: list[str], industry: str, keyword: str = "") -> list[dict[str, Any]]:
    domain = get_domain_pack(industry)
    niche = domain.get("niche") or domain.get("name") or industry
    seeds = domain.get("researchSeeds") or ["sai lầm phổ biến", "cách làm", "case study"]
    if domain.get("id") == "finance":
        sample = [
            {"platform": "youtube", "channel": "CFD Research Lab", "url": "https://youtube.com/watch?v=demo-liquidity", "title": "Liquidity Pool: Where Smart Money Hunts", "view_count": 482000, "like_count": 18400, "comment_count": 1200, "share_count": 3800},
            {"platform": "tiktok", "channel": "Trading Thực Chiến", "url": "https://tiktok.com/@demo/video/stop-loss", "title": "Stop Loss của bạn đang nằm ở đâu?", "view_count": 1200000, "like_count": 74000, "comment_count": 2800, "share_count": 11600},
            {"platform": "facebook", "channel": "Finance Case Study", "url": "https://facebook.com/reel/multitimeframe", "title": "3 sai lầm khi giao dịch đa khung", "view_count": 316000, "like_count": 9700, "comment_count": 846, "share_count": 2100},
        ]
    else:
        sample = [
            {"platform": "youtube", "channel": f"{domain.get('name', niche)} Lab", "url": "https://youtube.com/watch?v=brandflow-demo-1", "title": f"{seeds[0].title()}: điều ít người để ý trong {niche}", "view_count": 482000, "like_count": 18400, "comment_count": 1200, "share_count": 3800},
            {"platform": "tiktok", "channel": "Creator Thực Chiến", "url": "https://tiktok.com/@brandflow/video/demo-2", "title": f"3 {seeds[min(1, len(seeds)-1)]} giúp bạn tránh mất thời gian", "view_count": 1200000, "like_count": 74000, "comment_count": 2800, "share_count": 11600},
            {"platform": "facebook", "channel": "Case Study Việt Nam", "url": "https://facebook.com/reel/brandflow-demo-3", "title": f"Case study thật: áp dụng {seeds[min(2, len(seeds)-1)]} trong {niche}", "view_count": 316000, "like_count": 9700, "comment_count": 846, "share_count": 2100},
        ]
    selected = [item for item in sample if item["platform"] in platforms]
    return normalize_research_rows(selected, industry, keyword)


def _nested(item: dict[str, Any], path: str) -> Any:
    value: Any = item
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _first(item: dict[str, Any], *paths: str) -> Any:
    for path in paths:
        value = _nested(item, path)
        if value is not None and value != "":
            return value
    return None


def _metric_optional(item: dict[str, Any], *paths: str) -> int | None:
    value = _first(item, *paths)
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, str):
        try:
            return max(0, int(float(value.replace(",", ""))))
        except ValueError:
            return None
    return None


def _json_from_model(value: str) -> Any:
    value = re.sub(r"^```(?:json)?\s*", "", value.strip(), flags=re.I)
    value = re.sub(r"\s*```$", "", value)
    decoder = json.JSONDecoder()
    errors = []
    for index, character in enumerate(value):
        if character not in "[{":
            continue
        try:
            parsed, _ = decoder.raw_decode(value[index:])
            if isinstance(parsed, (dict, list)):
                return parsed
        except json.JSONDecodeError as exc:
            errors.append(str(exc))
    raise ValueError(errors[-1] if errors else "Model không trả JSON object hoặc array")


def _kyma_json(api_key: str, primary_model: str, fallback_model: str, system: str, user: str, max_tokens: int = 2200) -> tuple[Any, str]:
    errors = []
    for model in dict.fromkeys([primary_model, fallback_model]):
        try:
            response = requests.post(
                "https://kymaapi.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "temperature": 0.15, "max_tokens": max_tokens, "response_format": {"type": "json_object"}},
                timeout=150,
            )
            response.raise_for_status()
            message = response.json()["choices"][0]["message"]
            content = message.get("content") or message.get("reasoning_content") or message.get("reasoning") or ""
            if isinstance(content, list):
                content = "\n".join(str(part.get("text") if isinstance(part, dict) else part) for part in content)
            return _json_from_model(content), model
        except Exception as exc:
            errors.append(f"{model}: {exc}")
    raise RuntimeError("Kyma không thể xử lý dữ liệu: " + " | ".join(errors)[-700:])


def _apify_run(actor: str, token: str, body: dict[str, Any], on_status: Callable[[str], None] | None = None) -> list[dict[str, Any]]:
    """Start an async Actor run and poll it, avoiding the 300s sync endpoint cutoff."""
    response = None
    transient_statuses = {429, 500, 502, 503, 504}
    for attempt in range(1, 5):
        response = requests.post(
            f"https://api.apify.com/v2/acts/{actor}/runs",
            params={"token": token, "timeout": 1200},
            json=body,
            timeout=45,
        )
        if response.status_code not in transient_statuses or attempt == 4:
            break
        if on_status:
            on_status(f"Apify tạm lỗi HTTP {response.status_code}; đang thử lại ({attempt}/4)")
        time.sleep(min(30, attempt * 5))
    if not response.ok:
        raise RuntimeError(f"Apify actor {actor} không khởi chạy được (HTTP {response.status_code})")
    run = (response.json() or {}).get("data") or {}
    run_id = str(run.get("id") or "")
    dataset_id = str(run.get("defaultDatasetId") or "")
    if not run_id:
        raise RuntimeError(f"Apify actor {actor} không trả run ID")
    deadline = time.monotonic() + 20 * 60
    terminal_errors = {"FAILED", "ABORTED", "TIMED-OUT"}
    status_failures = 0
    while time.monotonic() < deadline:
        try:
            status_response = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}", params={"token": token}, timeout=30)
        except requests.RequestException as exc:
            status_failures += 1
            if status_failures >= 6:
                raise RuntimeError(f"Mất kết nối khi đọc trạng thái Apify: {exc}") from exc
            if on_status:
                on_status(f"Kết nối Apify tạm gián đoạn; đang thử lại ({status_failures}/6)")
            time.sleep(min(30, status_failures * 5))
            continue
        if status_response.status_code in transient_statuses:
            status_failures += 1
            if status_failures < 6:
                if on_status:
                    on_status(f"Apify tạm lỗi HTTP {status_response.status_code}; đang thử lại ({status_failures}/6)")
                time.sleep(min(30, status_failures * 5))
                continue
        if not status_response.ok:
            raise RuntimeError(f"Không đọc được trạng thái Apify run (HTTP {status_response.status_code})")
        status_failures = 0
        state = (status_response.json() or {}).get("data") or {}
        status = str(state.get("status") or "UNKNOWN")
        dataset_id = str(state.get("defaultDatasetId") or dataset_id)
        if on_status:
            on_status("đang thu thập dữ liệu" if status in {"READY", "RUNNING"} else status.lower())
        if status == "SUCCEEDED":
            break
        if status in terminal_errors:
            message = str(state.get("statusMessage") or "").strip()
            raise RuntimeError(f"Apify actor {actor} kết thúc với trạng thái {status}" + (f": {message}" if message else ""))
        time.sleep(5)
    else:
        raise RuntimeError(f"Apify actor {actor} chạy quá 20 phút; run vẫn được giữ trên Apify")
    if not dataset_id:
        raise RuntimeError(f"Apify actor {actor} không trả dataset ID")
    items_response = None
    for attempt in range(1, 5):
        items_response = requests.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items",
            params={"token": token, "clean": "true", "format": "json"},
            timeout=120,
        )
        if items_response.status_code not in transient_statuses or attempt == 4:
            break
        if on_status:
            on_status(f"Tải dataset tạm lỗi HTTP {items_response.status_code}; đang thử lại ({attempt}/4)")
        time.sleep(min(30, attempt * 5))
    if not items_response.ok:
        raise RuntimeError(f"Không tải được dataset Apify (HTTP {items_response.status_code})")
    payload = items_response.json()
    return payload if isinstance(payload, list) else []


def _period_start(period: str) -> str:
    days = {"30d": 30, "90d": 90, "6m": 183, "12m": 365}.get(period, 365)
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()


def _tiktok_profile(url: str) -> str:
    match = re.search(r"tiktok\.com/@([^/?#]+)", url, re.I)
    return match.group(1) if match else url


def _actor_request(platform: str, research_mode: str, queries: list[str], urls: list[str], limit: int, period: str) -> tuple[str, dict[str, Any]]:
    if platform == "youtube":
        date_filter = "month" if period == "30d" else "year"
        if research_mode == "channel":
            regular = max(1, round(limit * .7))
            shorts = max(1, limit - regular)
            return "streamers~youtube-scraper", {"startUrls": [{"url": url} for url in urls], "maxResults": regular, "maxResultsShorts": shorts, "maxResultStreams": 0, "sortVideosBy": "POPULAR", "dateFilter": date_filter}
        selected_queries = queries[:5]
        per_query = max(1, (limit + len(selected_queries) - 1) // max(1, len(selected_queries)))
        regular = max(1, round(per_query * .7))
        shorts = max(1, per_query - regular)
        return "streamers~youtube-scraper", {"searchQueries": selected_queries, "maxResults": regular, "maxResultsShorts": shorts, "maxResultStreams": 0, "sortingOrder": "relevance", "dateFilter": date_filter}
    if platform == "tiktok":
        if research_mode == "channel":
            return "clockworks~tiktok-scraper", {"profiles": [_tiktok_profile(url) for url in urls], "resultsPerPage": limit, "profileSorting": "popular", "oldestPostDateUnified": _period_start(period), "shouldDownloadVideos": False, "shouldDownloadCovers": False}
        return "clockworks~tiktok-scraper", {"searchQueries": queries[:5], "resultsPerPage": limit, "searchSection": "/video", "videoSearchSorting": "MOST_RELEVANT", "shouldDownloadVideos": False, "shouldDownloadCovers": False}
    if platform == "facebook":
        if research_mode == "channel":
            newer = {"30d": "30 days", "90d": "90 days", "6m": "6 months", "12m": "12 months"}.get(period, "12 months")
            return "apify~facebook-posts-scraper", {"startUrls": [{"url": url} for url in urls], "resultsLimit": limit, "captionText": False, "onlyPostsNewerThan": newer}
        post_range = {"30d": "30d", "90d": "90d"}.get(period)
        body = {"searchQueries": queries[:5], "maxPosts": limit}
        if post_range:
            body["postTimeRange"] = post_range
        return "simpleapi~facebook-posts-search-scraper", body
    raise ValueError(f"Nền tảng chưa hỗ trợ: {platform}")


def _normalize_apify_item(item: dict[str, Any], platform: str, industry: str) -> dict[str, Any] | None:
    title = str(_first(item, "title", "text", "description", "caption", "postText") or "Video không có tiêu đề").strip()
    url = str(_first(item, "url", "webVideoUrl", "webpage_url", "videoUrl", "postUrl") or "").strip()
    if not url:
        video_id = _first(item, "id", "videoId")
        if platform == "youtube" and video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
    if not url:
        return None
    views = _metric_optional(item, "viewCount", "views", "playCount", "play_count", "videoViewCount")
    likes = _metric_optional(item, "likes", "likeCount", "diggCount", "like_count", "reactionsCount")
    comments = _metric_optional(item, "commentsCount", "commentCount", "comments", "comment_count")
    shares = _metric_optional(item, "shareCount", "shares", "repostCount", "share_count")
    known_interactions = sum(value for value in (likes, comments, shares) if value is not None)
    engagement = round(known_interactions / views * 100, 2) if views else None
    channel = str(_first(item, "channelName", "channel", "authorMeta.name", "authorMeta.nickName", "pageName", "user.name", "ownerName", "uploader") or "Không rõ kênh")
    identifier = hashlib.sha256(f"{platform}:{url}".encode("utf-8")).hexdigest()[:16]
    return {
        "id": identifier, "platform": platform, "channel": channel, "industry": industry,
        "title": title[:220], "description": str(_first(item, "description", "text", "caption", "postText") or "")[:500], "url": url,
        "views": views, "views_text": compact_number(views) if views is not None else "—",
        "likes": likes, "likes_text": compact_number(likes) if likes is not None else "—",
        "comments": comments, "comments_text": compact_number(comments) if comments is not None else "—",
        "shares": shares, "shares_text": compact_number(shares) if shares is not None else "—",
        "engagement_pct": engagement, "timestamp": _first(item, "date", "createTimeISO", "timestamp", "publishedAt", "time"),
        "thumbnail": str(_first(item, "thumbnailUrl", "thumbnail", "coverUrl", "displayUrl", "image") or ""),
    }


def _performance_scores(rows: list[dict[str, Any]]) -> None:
    platform_medians: dict[str, float] = {}
    for platform in {row["platform"] for row in rows}:
        values = [row["views"] for row in rows if row["platform"] == platform and row.get("views") is not None and row["views"] > 0]
        platform_medians[platform] = statistics.median(values) if values else 1
    for row in rows:
        relative = (row.get("views") or 0) / max(1, platform_medians.get(row["platform"], 1))
        engagement = row.get("engagement_pct") or 0
        row["viral_score"] = min(100, round(40 + min(relative, 5) * 9 + min(engagement, 10) * 1.5))


def _expand_research_queries(api_key: str, niche: str, keyword: str, language: str, primary: str, fallback: str) -> tuple[list[str], str]:
    payload, model = _kyma_json(
        api_key, primary, fallback,
        "Bạn là chuyên gia truy vấn social video. Chỉ trả JSON object hợp lệ, không markdown.",
        f'Tạo 6 truy vấn tìm video sát ý định. Ngách: "{niche}". Từ khóa: "{keyword}". Ngôn ngữ ưu tiên: {language}. Bao gồm tiếng Việt và tối đa 2 truy vấn tiếng Anh chỉ khi giúp tăng độ phủ. Trả {{"queries":[string]}}.',
        700,
    )
    queries = [str(value).strip() for value in payload.get("queries", []) if str(value).strip()]
    return list(dict.fromkeys([f"{niche} {keyword}".strip(), *queries]))[:7], model


def _rerank_research(api_key: str, rows: list[dict[str, Any]], niche: str, keyword: str, language: str, primary: str, fallback: str) -> tuple[list[dict[str, Any]], str]:
    stop_words = {"va", "la", "cua", "cho", "voi", "tai", "sao", "nhung", "mot", "cac", "trong", "the", "nao"}
    def tokens(value: str) -> set[str]:
        normalized = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii").lower()
        return {token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 1 and token not in stop_words}

    intent_tokens = tokens(f"{niche} {keyword}")
    prepared = []
    for row in rows:
        haystack = f'{row.get("title", "")} {row.get("description", "")} {row.get("channel", "")}'
        haystack_tokens = tokens(haystack)
        coverage = len(intent_tokens & haystack_tokens) / max(1, len(intent_tokens))
        keyword_coverage = len(tokens(keyword) & haystack_tokens) / max(1, len(tokens(keyword)))
        local_relevance = min(100, round(coverage * 55 + keyword_coverage * 35 + min(100, float(row.get("viral_score") or 0)) * .1))
        prepared.append((local_relevance, row))
    prepared.sort(key=lambda pair: (pair[0], pair[1].get("views") or 0), reverse=True)
    candidate_rows = [row for _, row in prepared[:35]]
    local_scores = {row["id"]: score for score, row in prepared}
    ranked: dict[str, dict[str, Any]] = {}
    used_model = primary
    compact = [{"id": row["id"], "platform": row["platform"], "channel": row["channel"], "title": row["title"], "description": row["description"][:240]} for row in candidate_rows]
    try:
        payload, used_model = _kyma_json(
            api_key, primary, fallback,
            "Bạn là bộ lọc độ liên quan video. Chỉ trả JSON object hợp lệ, không markdown. Không ưu ái video chỉ vì nhiều view.",
            f'Ý định: ngách "{niche}", chủ đề "{keyword}". Ưu tiên nội dung tiếng {language}; vẫn giữ nội dung ngôn ngữ khác nếu thật sự sát. Chấm relevance 0-100. Loại nội dung trùng từ nhưng khác ý định. Viết reason tiếng Việt ngắn. INPUT={json.dumps(compact, ensure_ascii=False)}. Trả {{"items":[{{"id":string,"relevance":number,"reason":string}}]}}.',
            2600,
        )
        for item in payload.get("items", []):
            ranked[str(item.get("id"))] = item
    except RuntimeError:
        used_model = "local-relevance-fallback"
    output = []
    for row in candidate_rows:
        item = ranked.get(row["id"], {})
        relevance = max(0, min(100, int(float(item.get("relevance", local_scores.get(row["id"], 0)) or 0))))
        if relevance < 55:
            continue
        row["relevance_score"] = relevance
        row["viral_reason"] = str(item.get("reason") or viral_reason({**row, "comments": row.get("comments") or 0, "shares": row.get("shares") or 0, "engagement_pct": row.get("engagement_pct") or 0}))
        row["ranking_score"] = round(relevance * .72 + row["viral_score"] * .28, 2)
        output.append(row)
    return sorted(output, key=lambda row: (row["ranking_score"], row.get("views") or 0), reverse=True), used_model


def live_research(payload: dict[str, Any], progress: Callable[[int, str], None]) -> dict[str, Any]:
    research_mode = "channel" if payload.get("research_mode") == "channel" else "topic"
    urls = [str(value).strip() for value in payload.get("channel_urls", []) if str(value).strip()]
    platforms = [value for value in payload.get("platforms", []) if value in {"youtube", "tiktok", "facebook"}]
    if research_mode == "channel":
        if not urls:
            raise ValueError("Hãy nhập ít nhất một URL kênh đối thủ")
        detected = [platform_from_url(url) for url in urls]
        unsupported = [url for url, platform in zip(urls, detected) if platform == "unknown"]
        if unsupported:
            raise ValueError("Link kênh chưa được hỗ trợ: " + ", ".join(unsupported[:3]))
        platforms = list(dict.fromkeys(detected))
    elif not platforms:
        raise ValueError("Hãy chọn ít nhất một nền tảng")
    niche = str(payload.get("industry") or "").strip()
    keyword = str(payload.get("keyword") or "").strip()
    if research_mode == "topic" and (not niche or not keyword):
        raise ValueError("Hãy nhập đầy đủ từ khóa và ngành/ngách")
    secrets = load_secrets()
    token = str(payload.get("apify_token") or secrets.get("APIFY_API_TOKEN") or "").strip()
    kyma_key = str(payload.get("kyma_key") or secrets.get("KYMA_API_KEY") or "").strip()
    if not token:
        raise RuntimeError("Chưa cấu hình APIFY_API_TOKEN")
    if not kyma_key:
        raise RuntimeError("Chưa cấu hình KYMA_API_KEY để lọc độ liên quan")
    research_model = secrets.get("KYMA_RESEARCH_MODEL") or "gemini-2.5-flash"
    rerank_model = secrets.get("KYMA_RERANK_MODEL") or "qwen-3-32b"
    fallback_model = secrets.get("KYMA_FALLBACK_MODEL") or "deepseek-v4-flash"
    language = str(payload.get("language") or "Tiếng Việt")
    period = str(payload.get("period") or "12m")
    progress(8, "Kyma đang hiểu ý định và mở rộng truy vấn")
    queries, expansion_used = ([f"{niche} {keyword}".strip()], "not-needed") if research_mode == "channel" else _expand_research_queries(kyma_key, niche, keyword, language, research_model, fallback_model)
    raw_items: list[tuple[str, dict[str, Any]]] = []
    warnings = []
    per_platform = max(20, min(100, (100 + len(platforms) - 1) // max(1, len(platforms))))
    for index, platform in enumerate(platforms, start=1):
        platform_urls = [url for url in urls if platform_from_url(url) == platform]
        progress(18 + int((index - 1) / max(1, len(platforms)) * 45), f"Apify đang quét {platform.title()}")
        try:
            actor, actor_input = _actor_request(platform, research_mode, queries, platform_urls, per_platform, period)
            status_progress = 18 + int((index - 1) / max(1, len(platforms)) * 45)
            raw_items.extend((platform, item) for item in _apify_run(actor, token, actor_input, lambda message, p=platform, v=status_progress: progress(v, f"{p.title()}: {message}")))
        except Exception as exc:
            warnings.append(f"{platform.title()}: {str(exc)[:180]}")
    if not raw_items:
        raise RuntimeError("Apify không trả về video nào. " + " | ".join(warnings))
    progress(66, "Đang chuẩn hóa chỉ số thật từ các nền tảng")
    rows = [row for platform, item in raw_items if (row := _normalize_apify_item(item, platform, niche))]
    deduped = list({row["url"]: row for row in rows}.values())
    _performance_scores(deduped)
    if research_mode == "topic":
        progress(78, "Qwen đang lọc và xếp hạng độ liên quan")
        ranked, rerank_used = _rerank_research(kyma_key, deduped, niche, keyword, language, research_model, rerank_model)
    else:
        rerank_used = "not-needed"
        for row in deduped:
            row["viral_reason"] = viral_reason({**row, "comments": row.get("comments") or 0, "shares": row.get("shares") or 0, "engagement_pct": row.get("engagement_pct") or 0})
        ranked = sorted(deduped, key=lambda row: (row["viral_score"], row.get("views") or 0), reverse=True)
    selected = ranked[:20]
    if len(selected) < 20:
        warnings.append(f"Chỉ tìm thấy {len(selected)} video đạt điều kiện; hệ thống không chèn dữ liệu minh họa.")
    progress(94, "Đang hoàn thiện danh sách video nghiên cứu")
    return {"items": selected, "mode": "live", "provider": "Apify + Kyma", "candidate_count": len(deduped), "warning": " | ".join(warnings), "models": {"query_expansion": expansion_used, "rerank": rerank_used, "fallback": fallback_model}}


GENERIC_RISK_PATTERNS = [
    (re.compile(r"\b(cam kết|đảm bảo|chắc chắn)\b.*\b(kết quả|hiệu quả|thành công|tăng)\b", re.I), "Cam kết kết quả tuyệt đối"),
    (re.compile(r"\b100\s*%\b|không thể sai|không bao giờ thất bại", re.I), "Tuyên bố tuyệt đối hoặc tỷ lệ thiếu nguồn"),
    (re.compile(r"\b(chữa khỏi|điều trị dứt điểm|chẩn đoán chắc chắn)\b", re.I), "Tuyên bố y tế cần chuyên môn và bằng chứng"),
]

FINANCE_RISK_PATTERNS = [
    (re.compile(r"\b(cam kết|đảm bảo|chắc chắn)\b.*\b(lợi nhuận|thắng|tăng)\b", re.I), "Cam kết kết quả tài chính"),
    (re.compile(r"\b100\s*%\b|không thể thua|không bao giờ lỗ", re.I), "Tuyên bố tuyệt đối hoặc tỷ lệ thiếu nguồn"),
    (re.compile(r"\b(mua ngay|bán ngay|all[- ]?in)\b", re.I), "Kêu gọi giao dịch trực tiếp"),
]


def check_claims(text: str, domain: dict[str, Any] | str | None = None) -> list[dict[str, str]]:
    domain_pack = get_domain_pack(domain) if isinstance(domain, str) or domain is None else domain
    warnings = []
    patterns = list(GENERIC_RISK_PATTERNS)
    if domain_pack.get("id") == "finance":
        patterns.extend(FINANCE_RISK_PATTERNS)
    for pattern, label in patterns:
        match = pattern.search(text)
        if match:
            warnings.append({"level": "warning", "label": label, "excerpt": match.group(0)[:120]})
    if not warnings:
        warnings.append({"level": "ok", "label": f"Không phát hiện claim rủi ro theo bộ quy tắc {domain_pack.get('name', 'đa ngành')}", "excerpt": ""})
    return warnings


def demo_scripts(video: dict[str, Any], brand: dict[str, Any], domain: dict[str, Any] | str | None = None) -> list[dict[str, Any]]:
    domain_pack = get_domain_pack(domain) if isinstance(domain, str) or domain is None else domain
    niche = domain_pack.get("niche") or domain_pack.get("name") or "ngách đã chọn"
    proof = ", ".join((domain_pack.get("proofTypes") or ["case-study"])[:2])
    topic = video.get("title") or f"một sai lầm phổ biến trong {niche}"
    cta = brand.get("cta") or "Theo dõi kênh để xem thêm nội dung thực hành."
    variants = [
        ("Cảnh báo trực diện", f"Nếu bạn vẫn tiếp cận {topic} theo cách cũ, rất có thể bạn đang bỏ qua yếu tố quan trọng nhất."),
        ("Phản trực giác", f"Điều số đông tin về {topic} chưa chắc đúng trong mọi tình huống."),
        ("Case study nhanh", f"Cách làm này trông rất hợp lý — cho đến khi đặt {topic} vào một tình huống thực tế."),
    ]
    results = []
    for index, (angle, hook) in enumerate(variants, start=1):
        disclaimer = domain_pack.get("disclaimer") or ""
        text = f"{hook}\n\nTrong video này, chúng ta chỉ tập trung vào một cơ chế: xác định bối cảnh, chỉ ra điểm cần quan sát và kiểm chứng bằng {proof}. Hãy dùng bằng chứng phù hợp thay vì kết luận chỉ từ một ví dụ.\n\n{cta}" + (f"\n\n{disclaimer}" if disclaimer else "")
        results.append({
            "id": f"script-{index}", "angle": angle, "text": text,
            "analysis": {"hook": "Tạo tension ngay câu đầu", "body": "Một cơ chế, có trình tự", "visual": f"Chứng minh bằng {proof}", "cta": "Khớp cấu hình thương hiệu"},
            "claim_check": check_claims(text, domain_pack),
        })
    return results


def extract_json_block(value: str) -> Any:
    stripped = value.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.I)
    stripped = re.sub(r"\s*```$", "", stripped)
    return json.loads(stripped)


def live_scripts(video: dict[str, Any], brand: dict[str, Any], progress: Callable[[int, str], None], domain: dict[str, Any] | str | None = None) -> list[dict[str, Any]]:
    domain_pack = get_domain_pack(domain) if isinstance(domain, str) or domain is None else domain
    secrets = load_secrets()
    api_key = secrets.get("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("Chưa cấu hình LLM_API_KEY")
    base = (secrets.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = secrets.get("LLM_MODEL") or "gpt-4.1-mini"
    progress(20, "Đang phân tích video được chọn")
    prompt = f"""Bạn là biên tập viên video thương hiệu cá nhân cho nhiều ngành. Từ video nghiên cứu bên dưới, tạo đúng 3 kịch bản tiếng Việt nguyên bản, không sao chép câu chữ. Mỗi kịch bản dưới 60 giây, có hook, một cơ chế giải thích, hành động thực tế và CTA. Phân tích hook, body, visual proof và CTA. Tuân thủ toàn bộ quy tắc domain, không bịa dữ kiện hoặc kết quả.\n\nDOMAIN PACK: {json.dumps(domain_pack, ensure_ascii=False)}\nVIDEO: {json.dumps(video, ensure_ascii=False)}\nBRAND: {json.dumps(brand, ensure_ascii=False)}\n\nChỉ trả JSON array với field: id, angle, text, analysis (hook, body, visual, cta)."""
    response = requests.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
        timeout=120,
    )
    response.raise_for_status()
    progress(80, "Đang kiểm tra cấu trúc và claim")
    content = response.json()["choices"][0]["message"]["content"]
    scripts = extract_json_block(content)
    if not isinstance(scripts, list) or len(scripts) != 3:
        raise RuntimeError("LLM không trả đúng ba kịch bản")
    for index, script in enumerate(scripts, start=1):
        script.setdefault("id", f"script-{index}")
        script["claim_check"] = check_claims(str(script.get("text", "")), domain_pack)
    return scripts


def submit_heygen(project_folder: Path, payload: dict[str, Any], progress: Callable[[int, str], None]) -> dict[str, Any]:
    secrets = load_secrets()
    api_key = str(payload.get("heygen_key") or secrets.get("HEYGEN_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("Chưa cấu hình HEYGEN_API_KEY")
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json", "Accept": "application/json"}
    output = project_folder / "heygen_source.mp4"
    video_id_path = project_folder / "heygen_video_id.txt"
    if output.is_file() and output.stat().st_size > 0:
        return {"video_id": video_id_path.read_text(encoding="utf-8").strip() if video_id_path.exists() else "", "file": output.name, "size": output.stat().st_size, "resumed": True}
    if video_id_path.exists() and video_id_path.read_text(encoding="utf-8").strip():
        video_id = video_id_path.read_text(encoding="utf-8").strip()
        progress(20, f"Tiếp tục theo dõi HeyGen: {video_id}")
    else:
        video_id = ""
    voice_id = str(payload.get("voice_id") or "").strip()
    avatars = [str(value).strip() for value in payload.get("avatar_ids", []) if str(value).strip()]
    scenes = payload.get("scenes") or []
    if not video_id and (not voice_id or not avatars or not scenes):
        raise ValueError("Cần Voice ID, ít nhất một Avatar ID và kịch bản đã chia scene")
    if not video_id:
        inputs = []
        for index, scene in enumerate(scenes):
            inputs.append({
                "character": {"type": "avatar", "avatar_id": avatars[index % len(avatars)], "avatar_style": "normal"},
                "voice": {"type": "text", "input_text": str(scene.get("text") or scene), "voice_id": voice_id, "speed": float(payload.get("speed", 1.0))},
            })
        request_body = {"video_inputs": inputs, "dimension": {"width": 1080, "height": 1920}, "test": bool(payload.get("test", False))}
        write_json(project_folder / "heygen_request.json", {**request_body, "requested_engine": "photo-avatar-iii", "fallback_allowed": False, "video_inputs": [{**item, "voice": {**item["voice"], "voice_id": "***"}} for item in inputs]})
        progress(10, "Đang gửi job tới HeyGen")
        response = requests.post("https://api.heygen.com/v2/video/generate", headers=headers, json=request_body, timeout=60)
        response.raise_for_status()
        video_id = response.json()["data"]["video_id"]
        video_id_path.write_text(video_id, encoding="utf-8")
        progress(20, f"HeyGen đang render: {video_id}")
    transient_failures = 0
    deadline = time.time() + 3600
    while True:
        try:
            status_response = requests.get(f"https://api.heygen.com/v1/video_status.get?video_id={video_id}", headers=headers, timeout=60)
            status_response.raise_for_status()
            data = status_response.json()["data"]
            transient_failures = 0
        except requests.RequestException as exc:
            transient_failures += 1
            if transient_failures >= 8 or time.time() >= deadline:
                raise RuntimeError(f"Không thể kiểm tra trạng thái HeyGen sau nhiều lần thử: {exc}") from exc
            progress(25, f"Kết nối HeyGen tạm gián đoạn; đang thử lại ({transient_failures}/8)")
            time.sleep(min(45, 10 * transient_failures))
            continue
        status = data.get("status", "unknown")
        if status == "completed":
            video_url = data["video_url"]
            break
        if status in {"failed", "error"}:
            raise RuntimeError(f"HeyGen render thất bại: {data}")
        progress(25, f"HeyGen đang render ({status}); nhà cung cấp chưa trả phần trăm thực")
        time.sleep(15)
    progress(90, "Đang tải video HeyGen")
    with requests.get(video_url, stream=True, timeout=180) as download:
        download.raise_for_status()
        with output.open("wb") as handle:
            for chunk in download.iter_content(1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return {"video_id": video_id, "file": output.name, "size": output.stat().st_size, "resumed": video_id_path.exists()}


def create_noface_plan(project_folder: Path, payload: dict[str, Any]) -> dict[str, Any]:
    plan = {
        "schema_version": 1,
        "created_at": now_iso(),
        "route": "no-face",
        "voice_source": payload.get("voice_source", "tts"),
        "style": payload.get("style", "editorial-proof"),
        "target_seconds": payload.get("target_seconds", 55),
        "visual_mix": payload.get("visual_mix", {"technical_proof": 50, "real_world": 30, "stock_context": 20}),
        "scenes": payload.get("scenes", []),
        "status": "storyboard_required",
    }
    write_json(project_folder / "noface_plan.json", plan)
    return plan


def prepare_noface_source(project_folder: Path, payload: dict[str, Any], progress: Callable[[int, str], None]) -> dict[str, Any]:
    """Persist the no-face plan and return a real audio source for the edit pipeline."""
    plan = create_noface_plan(project_folder, payload)
    voice_source = str(payload.get("voice_source") or "tts").strip().lower()
    if voice_source == "approved-audio":
        secrets = load_secrets()
        api_key = str(payload.get("heygen_key") or secrets.get("HEYGEN_API_KEY") or "").strip()
        voice_id = str(payload.get("voice_id") or secrets.get("HEYGEN_VOICE_ID") or "").strip()
        avatar_ids = payload.get("avatar_ids") or [item.strip() for item in str(secrets.get("HEYGEN_AVATAR_ID") or "").split(",") if item.strip()]
        if not api_key or not voice_id or not avatar_ids:
            raise RuntimeError("Chưa cấu hình HEYGEN_API_KEY, HEYGEN_VOICE_ID hoặc HEYGEN_AVATAR_ID")
        script = read_json(project_folder / "approved_script.json", {}) or {}
        text = str(script.get("text") or "").strip()
        if not text:
            raise ValueError("Không có kịch bản đã duyệt để tạo HeyGen voice")
        speed = max(0.5, min(1.5, float(payload.get("speed") or 1)))
        scenes = payload.get("scenes") or [{"text": text}]
        progress(10, "Đang tạo source bằng HeyGen Voice ID đã duyệt")
        source_result = submit_heygen(project_folder, {"heygen_key": api_key, "voice_id": voice_id, "avatar_ids": avatar_ids, "scenes": scenes, "speed": speed, "test": bool(payload.get("test", True))}, progress)
        source_video = project_folder / source_result["file"]
        output = project_folder / "heygen_voice.mp3"
        progress(92, "Đang tách voice HeyGen cho timeline no-face")
        _run_engine(["ffmpeg", "-y", "-i", str(source_video), "-vn", "-c:a", "libmp3lame", "-b:a", "192k", str(output)], ROOT.parent, 600)
        plan.update(status="ready", source_file=output.name, voice_provider="heygen", voice_id="***", speed=speed, heygen_source_file=source_video.name)
        write_json(project_folder / "noface_plan.json", plan)
        progress(100, "Audio HeyGen cho video no-face đã sẵn sàng")
        return {"file": output.name, "size": output.stat().st_size, "plan": plan}
    if voice_source != "tts":
        source_name = str(payload.get("source_file") or "").strip()
        source = _safe_project_file(project_folder, source_name)
        if not source.is_file():
            raise FileNotFoundError("Không tìm thấy tệp giọng đọc đã tải lên")
        plan.update(status="ready", source_file=source_name)
        write_json(project_folder / "noface_plan.json", plan)
        progress(100, "Voice no-face đã sẵn sàng")
        return {"file": source_name, "plan": plan}

    script = read_json(project_folder / "approved_script.json", {}) or {}
    text = str(script.get("text") or "").strip()
    if not text:
        text = "\n\n".join(str(scene.get("text") if isinstance(scene, dict) else scene).strip() for scene in payload.get("scenes", [])).strip()
    if not text:
        raise ValueError("Không có kịch bản đã duyệt để tạo giọng AI")
    voice = str(payload.get("voice") or "vi-VN-HoaiMyNeural").strip()
    if not re.fullmatch(r"[A-Za-z]{2,3}-[A-Za-z]{2,4}-[A-Za-z0-9]+Neural", voice):
        raise ValueError("Giọng AI không hợp lệ")
    speed = max(0.5, min(1.5, float(payload.get("speed") or 1)))
    rate = round((speed - 1) * 100)
    output = project_folder / "noface_voice.mp3"
    progress(15, "Đang tạo giọng AI cho video no-face")
    command = [os.sys.executable, "-m", "edge_tts", "--voice", voice, "--rate", f"{rate:+d}%", "--text", text, "--write-media", str(output)]
    completed = subprocess.run(command, cwd=ROOT.parent, capture_output=True, text=True, timeout=300, check=False)
    if completed.returncode or not output.is_file() or output.stat().st_size == 0:
        detail = (completed.stderr or completed.stdout or "edge-tts không tạo được audio").strip()
        raise RuntimeError(f"Không thể tạo giọng AI: {detail[:240]}")
    plan.update(status="ready", source_file=output.name, voice=voice, speed=speed)
    write_json(project_folder / "noface_plan.json", plan)
    progress(100, "Giọng AI no-face đã sẵn sàng")
    return {"file": output.name, "size": output.stat().st_size, "plan": plan}


def build_edit_plan(project_folder: Path, payload: dict[str, Any], domain: dict[str, Any] | str | None = None) -> dict[str, Any]:
    domain_pack = get_domain_pack(domain) if isinstance(domain, str) or domain is None else domain
    style = get_edit_style(payload.get("style_id"), domain_pack)
    script = read_json(project_folder / "approved_script.json", {}) or {}
    text = str(script.get("text") or "").strip()
    segments = [item.strip() for item in re.split(r"\n+|(?<=[.!?])\s+", text) if item.strip()] or ["Bổ sung nội dung đã duyệt trước khi dựng."]
    duration = round(max(1.0, min(7200.0, float(payload.get("target_seconds") or 55))), 3)
    per_beat = duration / len(segments)
    proof_types = domain_pack.get("proofTypes") or ["owned-assets"]
    effects = style.get("textEffects") or ["fade-rise"]
    transitions = style.get("transitions") or ["clean-cut"]
    video_mode = str(payload.get("video_mode") or "avatar")
    # A number alone is not a reason to draw a chart. Reserve designed proof
    # visuals for narration that explicitly cites evidence or asks for a visual
    # comparison; numeric hooks, stories and advice work better as real footage.
    proof_cues = re.compile(r"\b(nghiên cứu (?:cho thấy|chỉ ra)|theo báo cáo|biểu đồ|chart|bằng chứng|so sánh|theo nguồn|dữ liệu cho thấy|đường xanh|đường đỏ)\b", re.I)
    context_cues = re.compile(r"\b(khi|lúc|trước đây|hằng ngày|mỗi ngày|trải nghiệm|câu chuyện|khách hàng|đội ngũ|quy trình|thực tế|tình huống|bắt đầu|thực hiện|làm việc)\b", re.I)
    metaphor_cues = re.compile(r"\b(giống như|tựa như|hình dung|chiếc|cánh cửa|cây cầu|nút thắt|đòn bẩy)\b", re.I)
    opinion_cues = re.compile(r"\b(tôi nghĩ|theo tôi|quan điểm|điều quan trọng|hãy nhớ|bài học)\b", re.I)
    beats = []
    for index, spoken in enumerate(segments):
        if video_mode != "noface" and (index == 0 or index == len(segments) - 1 or opinion_cues.search(spoken)):
            role = "presenter"
        elif proof_cues.search(spoken):
            role = "proof"
        elif metaphor_cues.search(spoken):
            role = "metaphor"
        elif context_cues.search(spoken):
            role = "context"
        elif video_mode == "noface":
            role = "context"
        else:
            role = "presenter"
        if role == "proof":
            asset_source, providers, reason, fallback, minimum_hold = proof_types[index % len(proof_types)], [], "Luận điểm cần bằng chứng trực quan thay vì stock trang trí.", "presenter-fullscreen-with-proof-typography", 2.0
        elif role == "context":
            asset_source, providers, reason, fallback, minimum_hold = "owned-assets", ["pexels", "pixabay"], "Câu mô tả bối cảnh hoặc hành động phù hợp B-roll đời sống.", "presenter-fullscreen-with-caption", 1.5
        elif role == "metaphor":
            asset_source, providers, reason, fallback, minimum_hold = "designed-visual-metaphor", [], "Ẩn dụ cần hình ảnh khớp chính xác với ý thoại.", "presenter-fullscreen-with-keyword-typography", 1.5
        else:
            asset_source, providers, reason, fallback, minimum_hold = ("brand-typography" if video_mode == "noface" else "approved-source-video"), [], "Giữ người nói để duy trì niềm tin, chuyển ý hoặc CTA.", "brand-typography-with-caption", 0.9
        source_order = ["owned-assets", "pexels", "pixabay", fallback] if role == "context" else [asset_source, fallback]
        beats.append({"id": f"beat-{index + 1}", "start": round(index * per_beat, 2), "end": round(min(duration, (index + 1) * per_beat), 2), "spoken_meaning": spoken, "visual_role": role, "asset_source": asset_source, "stock_providers": providers, "source_order": source_order, "cut_reason": reason, "minimum_hold_sec": minimum_hold, "caption_treatment": style.get("caption", "clean-two-line"), "text_effect": effects[index % len(effects)], "transition": transitions[index % len(transitions)], "audio_cue": "hook-hit" if index == 0 else "voice-first", "fallback": fallback})
    plan = {"schema_version": 2, "created_at": now_iso(), "video_mode": video_mode, "style": style, "domain_pack_id": domain_pack.get("id"), "proof_types": proof_types, "compliance": domain_pack.get("compliance") or [], "duration_seconds": duration, "verification": {"audio_is_timeline_source": True, "semantic_cuts_only": True, "full_visual_coverage_required": video_mode == "noface", "stock_provider_order": ["pexels", "pixabay"], "return_to_presenter_when_asset_ends": video_mode != "noface", "rotate_transition_flavors": True, "payoff_hold_min_sec": 1, "require_draft_frame_inspection": True, "require_final_spot_check": True}, "beats": beats, "status": "ready_for_multi_style_edit"}
    write_json(project_folder / "edit_plan.json", plan)
    return plan


def _run_engine(command: list[str], cwd: Path, timeout: int = 3600, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "Lệnh dựng video thất bại")[-3000:])
    return (result.stdout + "\n" + result.stderr)[-3000:]


def _safe_project_file(project_folder: Path, relative: str) -> Path:
    target = (project_folder / str(relative).replace("/", os.sep)).resolve()
    if target != project_folder.resolve() and project_folder.resolve() not in target.parents:
        raise ValueError("Đường dẫn source không hợp lệ")
    return target


def _media_duration_seconds(path: Path) -> float:
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if probe.returncode:
        raise RuntimeError("Không đọc được thời lượng video nguồn.")
    try:
        duration = float(probe.stdout.strip())
    except (TypeError, ValueError) as error:
        raise RuntimeError("Video nguồn không có thời lượng hợp lệ.") from error
    if duration <= 0:
        raise RuntimeError("Video nguồn không có thời lượng hợp lệ.")
    return round(duration, 3)


def _apply_voice_timing(plan: dict[str, Any], timestamp_rows: list[dict[str, Any]], media_duration: float) -> dict[str, Any]:
    """Replace estimated equal beat lengths with actual aligned narration timing."""
    beats = plan.get("beats") or []
    applied = 0
    for index, beat in enumerate(beats):
        if index >= len(timestamp_rows):
            break
        row = timestamp_rows[index]
        start = max(0.0, min(media_duration, float(row.get("start") or 0)))
        end = max(start, min(media_duration, float(row.get("end") or start)))
        if end - start < 0.12:
            continue
        beat["start"] = round(start, 3)
        beat["end"] = round(end, 3)
        beat["timing_source"] = "voice-alignment"
        beat["alignment_mode"] = row.get("alignment_mode") or "matched"
        beat["match_score"] = row.get("match_score")
        applied += 1
    plan["timing_source"] = "voice-alignment" if applied else "estimated"
    plan["voice_aligned_beats"] = applied
    plan["voice_alignment_rows"] = len(timestamp_rows)
    return plan


def meaningful_overlay_text(spoken: str, max_words: int = 12) -> str:
    """Return a complete, useful clause instead of a fixed word fragment."""
    text = re.sub(r"\s+", " ", str(spoken)).strip()
    text = re.sub(r"^(hãy\s+(?:nhìn|xem)\s+(?:biểu đồ|sơ đồ)(?:\s+này)?\s*:\s*)", "", text, flags=re.I)
    clauses = [part.strip(" ,;:-") for part in re.split(r"[.;!?]|\s+[–—]\s+", text) if part.strip(" ,;:-")]
    candidate = clauses[0] if clauses else text
    comma_parts = [part.strip() for part in candidate.split(",") if part.strip()]
    lowered = candidate.lower()
    if "đường xanh" in lowered and "đường đỏ" in lowered:
        candidate = ", ".join(comma_parts[:2])
    elif len(comma_parts) > 2 and comma_parts[1].lower().startswith(("theo báo cáo", "theo nghiên cứu", "theo dữ liệu")):
        candidate = ", ".join(comma_parts[1:3])
    elif len(comma_parts) > 1 and len(comma_parts[0].split()) < 6:
        candidate = ", ".join(comma_parts[:2])
    elif comma_parts and len(comma_parts[0].split()) >= 4:
        candidate = comma_parts[0]
    words = candidate.split()
    if len(words) <= max_words:
        return candidate
    if len(words) <= max_words + 2 and re.search(r"\d", " ".join(words[-2:])):
        return candidate
    for end in range(max_words, 5, -1):
        if words[end - 1].lower() in {"là", "vì", "và", "của", "cho", "với", "theo", "này", "đường"}:
            continue
        return " ".join(words[:end]).rstrip(" ,;:-")
    return " ".join(words[:max_words]).rstrip(" ,;:-")


def overlay_suppressed_beat_ids(manifest: dict[str, Any]) -> set[str]:
    """Technical visuals own their text hierarchy and must not be covered."""
    return {
        str(asset.get("beat_id"))
        for asset in manifest.get("assets", [])
        if asset.get("overlay_policy") == "suppress" or asset.get("provider") == "brandflow-local"
    }


def latest_reusable_render_version(project_folder: Path, requested_version: int, requested_style_id: str = "") -> int | None:
    versions = []
    for candidate in project_folder.glob("final-v*.mp4"):
        match = re.fullmatch(r"final-v(\d+)\.mp4", candidate.name)
        if not match:
            continue
        version = int(match.group(1))
        qa = read_json(project_folder / f"render_qa-v{version}.json", {}) or {}
        plan = read_json(project_folder / f"edit_plan-v{version}.json", {}) or {}
        completed_style_id = str((plan.get("style") or {}).get("id") or "")
        if (
            version >= requested_version
            and candidate.stat().st_size > 0
            and qa.get("technical_ok")
            and (not requested_style_id or completed_style_id == requested_style_id)
        ):
            versions.append(version)
    return max(versions) if versions else None


def render_edit(project_folder: Path, payload: dict[str, Any], progress: Callable[[int, str], None], domain: dict[str, Any] | str | None = None) -> dict[str, Any]:
    """Render a versioned MP4 from an approved source; never overwrite an earlier render."""
    source_name = str(payload.get("source_file") or "heygen_source.mp4")
    source = _safe_project_file(project_folder, source_name)
    if not source.is_file():
        raise FileNotFoundError(f"Không tìm thấy video nguồn trong project: {source_name}")
    suffix = source.suffix.lower()
    if suffix not in {".mp4", ".mov", ".m4v", ".webm", ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}:
        raise ValueError("Định dạng video/audio nguồn chưa được hỗ trợ")
    requested_version = max(1, int(payload.get("version") or 1))
    requested_style_id = str(payload.get("style_id") or "")
    reusable_version = latest_reusable_render_version(project_folder, requested_version, requested_style_id)
    if reusable_version is not None:
        requested_version = reusable_version
    completed_output = project_folder / f"final-v{requested_version}.mp4"
    completed_qa = read_json(project_folder / f"render_qa-v{requested_version}.json", {}) or {}
    completed_plan = read_json(project_folder / f"edit_plan-v{requested_version}.json", {}) or {}
    if completed_output.is_file() and completed_output.stat().st_size > 0 and completed_qa.get("technical_ok"):
        progress(100, f"Phiên bản {requested_version} đã dựng xong; đang mở lại kết quả")
        return {
            "file": completed_output.name,
            "version": requested_version,
            "size": completed_output.stat().st_size,
            "qa": completed_qa,
            "edit_plan": completed_plan,
            "media_manifest": f"media_manifest-v{requested_version}.json",
            "resumed": True,
        }
    version = requested_version
    while (project_folder / f"final-v{version}.mp4").exists():
        version += 1
    if suffix in {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}:
        progress(5, "Đang tạo nền dọc cho voice no-face")
        canvas = project_folder / f"noface-source-v{version}.mp4"
        _run_engine(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x0b0c0f:s=1080x1920:r=25", "-i", str(source), "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(canvas)], ROOT.parent, 1800)
        source = canvas
    progress(8, "Đang phân tích kịch bản và timeline giọng nói")
    domain_pack = get_domain_pack(domain) if isinstance(domain, str) or domain is None else domain
    requested_duration = float(payload.get("target_seconds") or 55)
    actual_duration = _media_duration_seconds(source)
    plan_payload = {**payload, "target_seconds": actual_duration}
    plan = build_edit_plan(project_folder, plan_payload, domain_pack)
    plan["requested_duration_seconds"] = requested_duration
    plan["duration_seconds"] = actual_duration
    plan["duration_source"] = "source_media"
    plan["version"] = version
    plan["output_spec"] = {"width": 1080, "height": 1920, "aspect_ratio": "9:16", "container": "mp4"}
    plan["feedback"] = str(payload.get("feedback") or "").strip()
    write_json(project_folder / f"edit_plan-v{version}.json", plan)
    write_json(project_folder / "edit_plan.json", plan)

    approved = read_json(project_folder / "approved_script.json", {}) or {}
    script_text = str(approved.get("text") or "").strip()
    phrases = [part.strip() for part in re.split(r"\n+|(?<=[.!?])\s+", script_text) if part.strip()]
    if not phrases:
        raise ValueError("Không có kịch bản đã duyệt để căn phụ đề")
    phrase_rows = [{"spoken": phrase, "display": phrase} for phrase in phrases]
    phrase_path = project_folder / f"subtitle_phrases-v{version}.json"
    timestamps = project_folder / f"timestamps-v{version}.json"
    captions_base = project_folder / f"captions-base-v{version}.ass"
    captions = project_folder / f"captions-v{version}.ass"
    transcript = project_folder / f"transcript-v{version}.txt"
    write_json(phrase_path, phrase_rows)

    engine_root = ROOT.parent / "engine"
    python = os.getenv("PYTHON_EXECUTABLE") or os.sys.executable
    progress(20, "Đang nhận diện lời nói và căn phụ đề theo audio thật")
    _run_engine([python, str(engine_root / "scripts" / "transcribe_align_news.py"), str(source), str(phrase_path), str(timestamps), str(captions_base), str(transcript), str(payload.get("whisper_model") or "base")], ROOT.parent, 3600)
    timestamp_rows = read_json(timestamps, []) or []
    plan = _apply_voice_timing(plan, timestamp_rows, actual_duration)
    write_json(project_folder / f"edit_plan-v{version}.json", plan)
    write_json(project_folder / "edit_plan.json", plan)
    progress(43, "Đang chia phụ đề thành các thẻ dễ đọc")
    style_palette = plan.get("style", {}).get("palette") or ["#060B16", "#B6FF36", "#F4F7EF"]
    _run_engine([
        python, str(engine_root / "scripts" / "generate_captions.py"), str(timestamps), str(captions),
        str(plan.get("style", {}).get("id") or "editorial-proof"), str(style_palette[1] if len(style_palette) > 1 else "#B6FF36"),
    ], ROOT.parent, 300)

    media_dir = project_folder / f"media-v{version}"
    slots = project_folder / f"broll_slots-v{version}.json"
    media_manifest = project_folder / f"media_manifest-v{version}.json"
    progress(52, "Đang chọn B-roll theo ngữ nghĩa: Pexels rồi Pixabay")
    stock_env = os.environ.copy()
    loaded = load_secrets()
    stock_env["PEXELS_API_KEY"] = str(payload.get("pexels_key") or loaded.get("PEXELS_API_KEY") or "")
    stock_env["PIXABAY_API_KEY"] = str(payload.get("pixabay_key") or loaded.get("PIXABAY_API_KEY") or "")
    _run_engine([python, str(engine_root / "scripts" / "stock_broll.py"), str(project_folder / "edit_plan.json"), "--media-dir", str(media_dir), "--slots", str(slots), "--manifest", str(media_manifest)], ROOT.parent, 1800, stock_env)

    overlay_input = payload.get("text_overlay") if isinstance(payload.get("text_overlay"), dict) else {}
    def safe_color(value: Any, fallback: str) -> str:
        candidate = str(value or "").strip().upper()
        return candidate if re.fullmatch(r"#[0-9A-F]{6}", candidate) else fallback
    overlay_settings = {
        "enabled": bool(overlay_input.get("enabled", True)),
        "preset": "finance-editorial",
        "kicker": str(overlay_input.get("kicker") or "ĐIỂM CẦN NHỚ").strip()[:60],
        "font_size": max(42, min(72, int(overlay_input.get("fontSize") or overlay_input.get("font_size") or 54))),
        "position": str(overlay_input.get("position") or "top") if str(overlay_input.get("position") or "top") in {"top", "middle", "lower"} else "top",
        "align": str(overlay_input.get("align") or "left") if str(overlay_input.get("align") or "left") in {"left", "center", "right"} else "left",
        "max_chars_per_line": max(16, min(34, int(overlay_input.get("maxCharsPerLine") or overlay_input.get("max_chars_per_line") or 24))),
        "text_color": safe_color(overlay_input.get("textColor") or overlay_input.get("text_color"), "#F4F7EF"),
        "accent_color": safe_color(overlay_input.get("accentColor") or overlay_input.get("accent_color"), "#B6FF36"),
        "background_color": safe_color(overlay_input.get("backgroundColor") or overlay_input.get("background_color"), "#060B16"),
        "background_opacity": max(0.2, min(0.8, float(overlay_input.get("backgroundOpacity") or overlay_input.get("background_opacity") or .58))),
        "accent_stripe": bool(overlay_input.get("accentStripe", overlay_input.get("accent_stripe", True))),
        "uppercase": bool(overlay_input.get("uppercase", True)),
    }
    custom_lines = overlay_input.get("lines") or []
    if isinstance(custom_lines, str):
        custom_lines = custom_lines.splitlines()
    custom_lines = [str(line).strip()[:140] for line in custom_lines if str(line).strip()][:20]
    overlays = []
    suppressed_overlay_beats = overlay_suppressed_beat_ids(read_json(media_manifest, {}) or {})
    if overlay_settings["enabled"]:
        for beat in plan.get("beats", []):
            if beat.get("visual_role") not in {"proof", "metaphor"}:
                continue
            if str(beat.get("id")) in suppressed_overlay_beats:
                continue
            custom_index = len(overlays)
            headline = custom_lines[custom_index] if custom_index < len(custom_lines) else meaningful_overlay_text(beat.get("spoken_meaning") or "")
            overlays.append({"kicker": overlay_settings["kicker"], "text": headline, "start": beat.get("start", 0), "end": beat.get("end", 0)})
    overlays_path = project_folder / f"text_overlays-v{version}.json"
    plan["text_overlay"] = {**overlay_settings, "items": overlays}
    write_json(project_folder / f"edit_plan-v{version}.json", plan)
    write_json(project_folder / "edit_plan.json", plan)
    write_json(overlays_path, {"settings": overlay_settings, "overlays": overlays})
    output = project_folder / f"final-v{version}.mp4"
    progress(68, "Đang dựng khung dọc 1080x1920, caption và visual")
    _run_engine([python, str(engine_root / "scripts" / "compose_video.py"), str(source), str(slots), str(media_dir), str(captions), str(payload.get("footer") or ""), str(output), str(overlays_path), str(project_folder / "edit_plan.json")], ROOT.parent, 7200)

    progress(93, "Đang kiểm tra kỹ thuật file MP4 thành phẩm")
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,duration", "-of", "json", str(output)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if probe.returncode:
        raise RuntimeError("Không đọc được thông số video thành phẩm")
    stream = (json.loads(probe.stdout).get("streams") or [{}])[0]
    technical_ok = int(stream.get("width") or 0) == 1080 and int(stream.get("height") or 0) == 1920 and output.stat().st_size > 0
    qa = {"version": version, "technical_ok": technical_ok, "width": stream.get("width"), "height": stream.get("height"), "duration": stream.get("duration"), "full_watch_required": True, "human_approved": False, "created_at": now_iso()}
    write_json(project_folder / f"render_qa-v{version}.json", qa)
    if not technical_ok:
        raise RuntimeError("Video render xong nhưng không đạt chuẩn 1080x1920")
    return {"file": output.name, "version": version, "size": output.stat().st_size, "qa": qa, "edit_plan": plan, "media_manifest": media_manifest.name}


def build_qa_report(project_folder: Path, payload: dict[str, Any], domain: dict[str, Any] | str | None = None) -> dict[str, Any]:
    domain_pack = get_domain_pack(domain) if isinstance(domain, str) or domain is None else domain
    required = ["full_watch", "caption_safe_area", "voice_alignment", "no_flash_frames", "source_traceability", "claims_checked"]
    checks = payload.get("checks") or {}
    normalized = {key: bool(checks.get(key)) for key in required}
    report = {"schema_version": 2, "checked_at": now_iso(), "domain_pack_id": domain_pack.get("id"), "checks": normalized, "warnings": payload.get("warnings") or [], "approved": all(normalized.values()) and bool(payload.get("approved")), "reviewer_note": str(payload.get("reviewer_note") or "").strip()}
    write_json(project_folder / "qa_report.json", report)
    return report


def publisher_command(project_folder: Path, payload: dict[str, Any], platform: str) -> list[str]:
    profile = str(payload.get("profile") or "cong")
    requested_video = str(payload.get("video") or "final.mp4")
    video = Path(requested_video).name
    if video != requested_video or not (project_folder / video).is_file():
        raise ValueError(f"Không tìm thấy video trong project: {requested_video}")
    schedule = payload.get("schedule")
    if platform == "facebook":
        command = ["python", str(PROJECT_ROOT / "scripts" / "publishers" / "facebook.py"), str(project_folder), "--profile", profile, "--video", video]
        if schedule:
            command += ["--schedule", str(schedule)]
        return command
    if platform == "youtube":
        command = ["python", str(PROJECT_ROOT / "scripts" / "publishers" / "youtube_playwright.py"), str(project_folder), "--video", video, "--privacy", str(payload.get("privacy") or "public")]
        if schedule:
            command += ["--schedule", str(schedule)]
        return command
    if platform == "tiktok":
        return ["python", str(PROJECT_ROOT / "scripts" / "publishers" / "tiktok.py"), str(project_folder), "--profile", profile, "--video", video]
    raise ValueError(f"Nền tảng không hỗ trợ: {platform}")


def run_publish(project_folder: Path, payload: dict[str, Any], progress: Callable[[int, str], None]) -> dict[str, Any]:
    if not payload.get("confirmed"):
        raise PermissionError("Cần xác nhận cuối trước khi đăng")
    platforms = payload.get("platforms") or []
    if not platforms:
        raise ValueError("Hãy chọn ít nhất một nền tảng")
    schedule = str(payload.get("schedule") or "").strip()
    if payload.get("mode") == "schedule" and not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", schedule):
        raise ValueError("Lịch đăng phải có dạng YYYY-MM-DD HH:MM")
    results = {}
    for index, platform in enumerate(platforms, start=1):
        progress(int((index - 1) / max(1, len(platforms)) * 90), f"Đang xử lý {platform}")
        command = publisher_command(project_folder, payload, platform)
        result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
        results[platform] = {"ok": result.returncode == 0, "output": (result.stdout + "\n" + result.stderr)[-3000:]}
        if result.returncode:
            break
    write_json(project_folder / "publish.json", {"published_at": now_iso(), "results": results, "request": {k: v for k, v in payload.items() if "token" not in k.lower()}})
    return results


PROJECTS = ProjectStore()
JOBS = JobManager()
