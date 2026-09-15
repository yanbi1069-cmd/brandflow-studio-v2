# Test local BrandFlow Studio V2

Tài liệu này kiểm tra hai lớp: regression không tốn phí và luồng live có chủ đích. Không chạy HeyGen, Kyma, Apify, Pexels hoặc Pixabay nếu chủ tài khoản chưa xác nhận chi phí/quota.

## 1. Chuẩn bị

- Node.js 20.9+, npm và Python 3.11+.
- FFmpeg/`ffprobe` có trong `PATH` nếu test render.
- Repo đã cài dependencies:

```powershell
npm install
python -m pip install -r local-agent/requirements.txt
Copy-Item .env.example .env.local
```

Tự điền key trong `.env.local` trên máy test. Không dán key vào issue, chat, ảnh chụp màn hình hoặc log được commit.

## 2. Kiểm tra tự động, không tốn API

```powershell
npm test
npm run build
python -m unittest discover -s local-agent/tests -v
python -m unittest discover -s engine/tests -v
python -m py_compile local-agent/agent_core.py engine/scripts/stock_broll.py engine/scripts/technical_broll.py engine/scripts/compose_video.py
```

Kỳ vọng Node tests đều pass, Next.js build thành công, Python không báo lỗi và không có request đến nhà cung cấp trả phí.

## 3. Khởi động local

```powershell
npm run dev:full
```

Mở:

- `http://localhost:3000/multi-niche`
- `http://127.0.0.1:8765/api/health`

Kỳ vọng frontend tải được và health endpoint trả HTTP 200.

## 4. Smoke test Demo mode

1. Mở studio đa ngành.
2. Nhập keyword và niche mẫu.
3. Chạy research demo, chọn một video và đưa vào hàng đợi.
4. Tạo ba kịch bản, duyệt một bản.
5. Chọn no-face hoặc upload một video test local.
6. Mở Edit, chọn style. Overlay Finance Editorial được ghép mặc định trên video, không có bảng chỉnh overlay trong UI.
7. Xác nhận trạng thái/nút điều hướng hoạt động đến QA.

Không bấm thao tác live nếu giao diện thông báo sẽ dùng API key/credit.

## 5. Test live end-to-end

Chỉ thực hiện sau khi chủ tài khoản xác nhận cho phép dùng API có thể phát sinh phí.

1. Tại Settings, kiểm tra cấu hình đã được nhận nhưng không để UI/log hiển thị toàn bộ key.
2. Research bằng `keyword + niche` hoặc URL kênh đối thủ.
3. Kiểm tra bảng có kênh, URL, view, like, comment, share, tương tác và lý do nổi bật. Trường không được nền tảng cung cấp phải hiển thị trạng thái phù hợp, không bịa số.
4. Chọn video, đưa vào hàng đợi và tạo ba kịch bản.
5. Duyệt một kịch bản.
6. Chọn HeyGen Photo Avatar III, no-face hoặc upload video gốc.
7. Với HeyGen, xác nhận riêng trước khi tạo; chờ job hoàn tất và kiểm tra source video mở được.
8. Chọn style edit rồi render; stock chỉ dùng cho cảnh cụ thể, đồ họa kỹ thuật được tạo local đúng mốc lời thoại.
9. Khi render, UI phải hiển thị `Đang edit…` cho tới khi job kết thúc.
10. Mở QA, kiểm tra kết quả và tải MP4.

## 6. Ma trận QA video

| Hạng mục | Tiêu chí đạt |
|---|---|
| Khung hình | 1080×1920, video dọc |
| Playback | MP4 mở được, không hỏng frame |
| Audio | Có tiếng, không clipping rõ rệt, đồng bộ hình |
| Caption | Đọc được, đúng nhịp, không tràn safe area |
| B-roll | Cảnh vật lý/đồ họa kỹ thuật khớp lời đọc ở đúng mốc; ý trừu tượng không bị ghép stock chung chung |
| Technical proof | Sơ đồ hoặc biểu đồ có chuyển động rõ, không giả làm dữ liệu thực |
| Kicker | Nhỏ, màu lime/accent đã chọn |
| Headline | Lớn, tương phản tốt |
| Background | Nền tối bán trong suốt theo preset mặc định |
| Placement | Overlay mặc định không che mặt/phụ đề |
| Accent stripe | Đúng màu lime của preset |
| Subject safety | Không che mặt hoặc chi tiết chính |
| Download | Route xem/tải trả HTTP 200 |

Kiểm tra metadata nhanh:

```powershell
ffprobe -v error -show_entries stream=width,height,duration -of default=noprint_wrappers=1 path\to\final-v2.mp4
```

## 7. Kiểm tra Git trước khi phát hành

```powershell
git status --short
git ls-files | Select-String -Pattern '\.env\.local$|local-agent/workspace|\.mp4$|\.wav$|node_modules|\.next'
```

Lệnh thứ hai không được trả về secret, workspace hoặc generated media. `.env.example` được phép vì chỉ chứa tên biến và giá trị mẫu không nhạy cảm.

## 8. Xử lý lỗi nhanh

- Frontend không lên: kiểm tra Node version, `npm install` và port 3000.
- Agent không health: cài `local-agent/requirements.txt`, kiểm tra Python và port 8765.
- Render lỗi: chạy `ffmpeg -version` và `ffprobe -version`; kiểm tra source video tồn tại.
- B-roll trống: ý trừu tượng sẽ giữ người dẫn theo thiết kế; với cảnh stock cụ thể, kiểm tra key Pexels/Pixabay (Pixabay tùy chọn). Đồ họa kỹ thuật dùng Pillow và FFmpeg local.
- HeyGen chờ lâu: theo dõi job, không gửi lại nhiều request tạo video.
- Overlay lỗi: giữ artifact local, kiểm tra edit request và filter compose trước khi render lại.
