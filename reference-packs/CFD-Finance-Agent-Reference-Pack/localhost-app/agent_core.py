from __future__ import annotations

import json
import os
import re
import statistics
import subprocess
import threading
import time
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import requests
from dotenv import dotenv_values, load_dotenv


ROOT = Path(__file__).resolve().parent
DEFAULTS_PATH = ROOT / "config" / "defaults.json"
ENV_PATH = ROOT / ".env"
DATA_DIR = ROOT / "data"
WORKSPACE = Path(os.getenv("CFD_AGENT_WORKSPACE") or ROOT / "workspace").resolve()
PROJECT_ROOT = Path(os.getenv("CFD_AGENT_PROJECT_ROOT") or ROOT.parents[1]).resolve()


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
    load_dotenv(ENV_PATH, override=False)
    values = {k: str(v or "") for k, v in dotenv_values(ENV_PATH).items()}
    for key in ("APIFY_API_TOKEN", "HEYGEN_API_KEY", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
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
        "llm": bool(secrets.get("LLM_API_KEY")),
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

    def create(self, title: str, selected_video: dict[str, Any] | None = None) -> dict[str, Any]:
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

        threading.Thread(target=runner, daemon=True, name=f"cfd-agent-{job_id}").start()
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
    sample = [
        {"platform": "youtube", "url": "https://youtube.com/watch?v=demo-liquidity", "title": "Liquidity Pool: Where Smart Money Hunts", "view_count": 482000, "like_count": 18400, "comment_count": 1200, "share_count": 3800},
        {"platform": "tiktok", "url": "https://tiktok.com/@demo/video/stop-loss", "title": "Stop Loss của bạn đang nằm ở đâu?", "view_count": 1200000, "like_count": 74000, "comment_count": 2800, "share_count": 11600},
        {"platform": "facebook", "url": "https://facebook.com/reel/multitimeframe", "title": "3 sai lầm khi giao dịch đa khung", "view_count": 316000, "like_count": 9700, "comment_count": 846, "share_count": 2100},
    ]
    selected = [item for item in sample if item["platform"] in platforms]
    return normalize_research_rows(selected, industry, keyword)


def live_research(payload: dict[str, Any], progress: Callable[[int, str], None]) -> list[dict[str, Any]]:
    urls = [str(value).strip() for value in payload.get("channel_urls", []) if str(value).strip()]
    if not urls:
        raise ValueError("Hãy nhập ít nhất một URL kênh đối thủ")
    platforms = set(payload.get("platforms") or [])
    max_videos = max(1, min(50, int(payload.get("max_videos", 20))))
    raw_items: list[dict[str, Any]] = []
    for index, url in enumerate(urls, start=1):
        platform = platform_from_url(url)
        if platform not in platforms:
            continue
        progress(int((index - 1) / len(urls) * 75), f"Đang đọc {platform}: {url}")
        command = [
            "yt-dlp", "--dump-json", "--skip-download", "--ignore-errors", "--no-warnings",
            "--playlist-end", str(max_videos), url,
        ]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        for line in result.stdout.splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            item["platform"] = platform
            raw_items.append(item)
        if result.returncode and not raw_items:
            raise RuntimeError(result.stderr[-500:] or f"Không đọc được kênh {url}")
    progress(85, "Đang chuẩn hóa chỉ số và phân tích viral")
    rows = normalize_research_rows(raw_items, str(payload.get("industry") or "cfd-finance"), str(payload.get("keyword") or ""))
    sort_by = payload.get("sort", "viral")
    key = {"views": "views", "engagement": "engagement_pct", "viral": "viral_score"}.get(sort_by, "viral_score")
    return sorted(rows, key=lambda row: row[key], reverse=True)


RISK_PATTERNS = [
    (re.compile(r"\b(cam kết|đảm bảo|chắc chắn)\b.*\b(lợi nhuận|thắng|tăng)\b", re.I), "Cam kết kết quả tài chính"),
    (re.compile(r"\b100\s*%\b|không thể thua|không bao giờ lỗ", re.I), "Tuyên bố tuyệt đối hoặc tỷ lệ thiếu nguồn"),
    (re.compile(r"\b(mua ngay|bán ngay|all[- ]?in)\b", re.I), "Kêu gọi giao dịch trực tiếp"),
]


def check_claims(text: str) -> list[dict[str, str]]:
    warnings = []
    for pattern, label in RISK_PATTERNS:
        match = pattern.search(text)
        if match:
            warnings.append({"level": "warning", "label": label, "excerpt": match.group(0)[:120]})
    if not warnings:
        warnings.append({"level": "ok", "label": "Không phát hiện cam kết lợi nhuận hoặc chỉ dẫn giao dịch trực tiếp", "excerpt": ""})
    return warnings


def demo_scripts(video: dict[str, Any], brand: dict[str, Any]) -> list[dict[str, Any]]:
    topic = video.get("title") or "một sai lầm phổ biến trong CFD"
    cta = brand.get("cta") or "Theo dõi kênh để xem thêm nội dung thực hành."
    variants = [
        ("Cảnh báo trực diện", f"Nếu bạn vẫn nhìn {topic} theo cách cũ, rất có thể bạn đang bỏ qua nơi dòng tiền thật sự tập trung."),
        ("Phản trực giác", f"Điều phần lớn trader tin về {topic} chưa chắc là điều thị trường đang thể hiện."),
        ("Case study nhanh", f"Setup này nhìn rất đẹp — cho đến khi bạn đặt {topic} vào đúng bối cảnh thị trường."),
    ]
    results = []
    for index, (angle, hook) in enumerate(variants, start=1):
        text = f"{hook}\n\nTrong video này, chúng ta chỉ tập trung vào một cơ chế: xác định bối cảnh, tìm vùng cần quan sát và chờ tín hiệu xác nhận. Hãy dùng chart như bằng chứng, không vào lệnh chỉ vì một pattern trông quen mắt.\n\n{cta}"
        results.append({
            "id": f"script-{index}", "angle": angle, "text": text,
            "analysis": {"hook": "Tạo tension ngay câu đầu", "body": "Một cơ chế, có trình tự", "visual": "Có thể chứng minh bằng chart", "cta": "Khớp cấu hình thương hiệu"},
            "claim_check": check_claims(text),
        })
    return results


def extract_json_block(value: str) -> Any:
    stripped = value.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.I)
    stripped = re.sub(r"\s*```$", "", stripped)
    return json.loads(stripped)


def live_scripts(video: dict[str, Any], brand: dict[str, Any], progress: Callable[[int, str], None]) -> list[dict[str, Any]]:
    secrets = load_secrets()
    api_key = secrets.get("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("Chưa cấu hình LLM_API_KEY")
    base = (secrets.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = secrets.get("LLM_MODEL") or "gpt-4.1-mini"
    progress(20, "Đang phân tích video được chọn")
    prompt = f"""Bạn là biên tập viên video ngắn CFD/Trading/Finance. Từ video nghiên cứu bên dưới, tạo đúng 3 kịch bản tiếng Việt nguyên bản, không sao chép câu chữ. Mỗi kịch bản dưới 60 giây, có hook, một cơ chế giải thích, hành động thực tế và CTA. Phân tích điểm hay của hook, body, visual proof và CTA. Tránh cam kết lợi nhuận hay lời khuyên mua/bán trực tiếp.\n\nVIDEO: {json.dumps(video, ensure_ascii=False)}\nBRAND: {json.dumps(brand, ensure_ascii=False)}\n\nChỉ trả JSON array với field: id, angle, text, analysis (hook, body, visual, cta)."""
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
        script["claim_check"] = check_claims(str(script.get("text", "")))
    return scripts


def submit_heygen(project_folder: Path, payload: dict[str, Any], progress: Callable[[int, str], None]) -> dict[str, Any]:
    secrets = load_secrets()
    api_key = secrets.get("HEYGEN_API_KEY")
    if not api_key:
        raise RuntimeError("Chưa cấu hình HEYGEN_API_KEY")
    voice_id = str(payload.get("voice_id") or "").strip()
    avatars = [str(value).strip() for value in payload.get("avatar_ids", []) if str(value).strip()]
    scenes = payload.get("scenes") or []
    if not voice_id or not avatars or not scenes:
        raise ValueError("Cần Voice ID, ít nhất một Avatar ID và kịch bản đã chia scene")
    inputs = []
    for index, scene in enumerate(scenes):
        inputs.append({
            "character": {"type": "avatar", "avatar_id": avatars[index % len(avatars)], "avatar_style": "normal"},
            "voice": {"type": "text", "input_text": str(scene.get("text") or scene), "voice_id": voice_id, "speed": float(payload.get("speed", 1.0))},
        })
    request_body = {"video_inputs": inputs, "dimension": {"width": 720, "height": 1280}, "test": bool(payload.get("test", False))}
    write_json(project_folder / "heygen_request.json", {**request_body, "video_inputs": [{**item, "voice": {**item["voice"], "voice_id": "***"}} for item in inputs]})
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json", "Accept": "application/json"}
    progress(10, "Đang gửi job tới HeyGen")
    response = requests.post("https://api.heygen.com/v2/video/generate", headers=headers, json=request_body, timeout=30)
    response.raise_for_status()
    video_id = response.json()["data"]["video_id"]
    (project_folder / "heygen_video_id.txt").write_text(video_id, encoding="utf-8")
    progress(20, f"HeyGen đang render: {video_id}")
    while True:
        status_response = requests.get(f"https://api.heygen.com/v1/video_status.get?video_id={video_id}", headers=headers, timeout=30)
        status_response.raise_for_status()
        data = status_response.json()["data"]
        status = data.get("status", "unknown")
        if status == "completed":
            video_url = data["video_url"]
            break
        if status in {"failed", "error"}:
            raise RuntimeError(f"HeyGen render thất bại: {data}")
        progress(min(85, 25 + int((time.time() % 60))), f"HeyGen: {status}")
        time.sleep(15)
    progress(90, "Đang tải video HeyGen")
    output = project_folder / "heygen_source.mp4"
    with requests.get(video_url, stream=True, timeout=180) as download:
        download.raise_for_status()
        with output.open("wb") as handle:
            for chunk in download.iter_content(1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return {"video_id": video_id, "file": output.name, "size": output.stat().st_size}


def create_noface_plan(project_folder: Path, payload: dict[str, Any]) -> dict[str, Any]:
    plan = {
        "schema_version": 1,
        "created_at": now_iso(),
        "route": "no-face",
        "voice_source": payload.get("voice_source", "tts"),
        "style": payload.get("style", "finance-editorial"),
        "target_seconds": payload.get("target_seconds", 55),
        "visual_mix": payload.get("visual_mix", {"technical_proof": 50, "real_world": 30, "stock_context": 20}),
        "scenes": payload.get("scenes", []),
        "status": "storyboard_required",
    }
    write_json(project_folder / "noface_plan.json", plan)
    return plan


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
