# CFD Finance Local Agent

Ứng dụng localhost đóng gói luồng sản xuất video thương hiệu cá nhân ngách CFD, trading và finance:

`Research → duyệt video → 3 kịch bản → duyệt → HeyGen / No-face / Upload → Finance Editorial Edit → feedback → tải file → đăng hoặc Skip`

Giao diện mặc định mở **Quy trình làm việc** để thao tác ngay. **Bản đồ vận hành** là một tab riêng ở sidebar; bấm một bước trên bản đồ sẽ mở đúng workbench tương ứng.

## Chạy nhanh trên Windows

1. Cài Python 3.11+ và FFmpeg.
2. Mở thư mục này, chạy `start-agent.cmd`.
3. Trình duyệt mở tại `http://127.0.0.1:8765/`.

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

Copy `.env.example` thành `.env` nếu muốn cấu hình thủ công. Không commit `.env`.

## Artifact theo project

Mỗi video nằm trong `workspace/content/YYYY-MM-DD/<slug>/`. Các file quan trọng:

- `selected_video.json`
- `script_candidates.json`
- `approved_script.json` và `voice_script_heygen.txt`
- `heygen_request.json`, `heygen_video_id.txt`, `heygen_source.mp4`; hoặc `noface_plan.json`
- `EDIT_REQUEST.md`, `edit_request.json`, `edit_feedback.json`
- `final.mp4`, `NOI_DUNG_DANG_BAI.txt`, `meta.json`, `publish.json`

Phiếu `EDIT_REQUEST.md` được thiết kế để skill `finance-editorial-edit` trong project nhận và dựng theo training pack `workspace/share/nhi-finance-editorial-training-pack`.

## Giới hạn hiện tại

- App tự tạo và quản lý artifact; bước dựng sáng tạo được chuyển giao cho Codex + skill `finance-editorial-edit`, không giả lập rằng một nút web đã hoàn tất edit.
- Research chỉ đọc dữ liệu mà nền tảng cho phép công khai; số share có thể không có trên một số nguồn.
- TikTok publishing có thể phải dùng package đăng thủ công khi Content Posting API chưa hoạt động.
- Trước khi đăng thật, cần có `final.mp4`, metadata và credentials của profile tương ứng.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
node --check static/app.js
```
