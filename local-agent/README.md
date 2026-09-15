# Personal Brand Video Agent — Finance-compatible multi-niche

Local-agent chạy research Apify + nhiều model Kyma theo job nền, HeyGen Photo Avatar III qua API legacy v2 (không tự fallback sang Avatar IV), và dựng MP4 dọc 1080×1920 theo phiên bản. Trạng thái job là các giai đoạn thật; khi nhà cung cấp không trả phần trăm render, UI chỉ hiển thị spinner, mô tả tác vụ và thời gian đã chạy.

Ứng dụng localhost giữ nguyên luồng Finance đã hoàn thiện và mở rộng bằng domain pack cho nhiều ngành:

`Research → duyệt video → 3 kịch bản → duyệt → HeyGen / No-face / Upload → Multi-style Edit → feedback → QA → tải file → đăng hoặc Skip`

Giao diện mặc định mở **Quy trình làm việc** để thao tác ngay. **Bản đồ vận hành** là một tab riêng ở sidebar; bấm một bước trên bản đồ sẽ mở đúng workbench tương ứng.

## Chạy nhanh trên Windows

1. Cài Python 3.11+ và FFmpeg.
2. Mở thư mục này, chạy `start-agent.cmd`.
3. Truy cập `http://127.0.0.1:8765/` sẽ tự chuyển sang Studio đa ngách tại
   `http://localhost:3000/multi-niche`. Port `8765` tiếp tục chạy engine/API nền.

Hoặc chạy:

```powershell
python -m pip install -r requirements.txt
python start_agent.py
```

## Chế độ dữ liệu

- **Demo**: kiểm tra toàn bộ UI và checkpoint, không gọi nền tảng ngoài.
- **Live research**: nhập URL kênh công khai, dùng `yt-dlp` để đọc metadata. Facebook/TikTok có thể giới hạn dữ liệu hoặc yêu cầu phiên đăng nhập.
- **Live script**: cấu hình `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` trong `.env` hoặc qua API settings.
- **HeyGen**: API key lưu cục bộ trong `.env`; mọi render đều cần xác nhận tại thời điểm bấm chạy.

Local-agent tự đọc `.env.local` ở thư mục gốc project, sau đó mới đọc `local-agent/.env` để hỗ trợ cấu hình riêng. Không commit hai file này.

## Artifact theo project

Mỗi video nằm trong `workspace/content/YYYY-MM-DD/<slug>/`. Các file quan trọng:

- `selected_video.json`
- `script_candidates.json`
- `approved_script.json` và `voice_script_heygen.txt`
- `heygen_request.json`, `heygen_video_id.txt`, `heygen_source.mp4`; hoặc `noface_plan.json`
- `EDIT_REQUEST.md`, `edit_request.json`, `edit_plan.json`, `edit_feedback.json`
- `qa_report.json`
- `final.mp4`, `NOI_DUNG_DANG_BAI.txt`, `meta.json`, `publish.json` hoặc `skip.json`

Phiếu `EDIT_REQUEST.md` được thiết kế để skill `multi-style-video-editor` nhận cùng `edit_plan.json`. Domain Finance vẫn dùng training pack `nhi-finance-editorial-training-pack` làm baseline.

## Giới hạn hiện tại

- App tự tạo và quản lý artifact; bước dựng sáng tạo được chuyển giao cho Codex + skill `multi-style-video-editor`, không giả lập rằng một nút web đã hoàn tất edit.
- Research chỉ đọc dữ liệu mà nền tảng cho phép công khai; số share có thể không có trên một số nguồn.
- TikTok publishing có thể phải dùng package đăng thủ công khi Content Posting API chưa hoạt động.
- Trước khi đăng thật, cần có `final.mp4`, metadata và credentials của profile tương ứng.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
node --check static/app.js
```
