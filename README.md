# BrandFlow Studio V2

Agent tạo video thương hiệu cá nhân đa ngành, vận hành theo luồng khép kín:

`Research → Script → Source Video → Edit → Final`

BrandFlow Studio V2 kết hợp Next.js studio với local Python agent để research nội dung, tạo ba phương án kịch bản, nhận video từ HeyGen Photo Avatar III/no-face/upload, dựng video dọc 1080×1920, kiểm tra QA và tải MP4. API key chỉ được xử lý qua proxy/local agent và không xuất hiện trong frontend.

## Tính năng chính

- Research theo từ khóa + ngành hoặc URL kênh đối thủ.
- Bảng kết quả có kênh, link, view, like, comment, share, tương tác và lý do nổi bật.
- Sinh ba kịch bản từ video đã duyệt bằng nhiều model Kyma có fallback.
- Ba nguồn video: HeyGen Photo Avatar III, no-face hoặc upload video gốc.
- Stock B-roll cho cảnh cụ thể: tìm bằng ý hình ảnh ngắn gọn, ưu tiên Pexels và fallback Pixabay; ý trừu tượng giữ người dẫn thay vì chèn stock sai lời.
- B-roll kỹ thuật (sơ đồ, biểu đồ minh họa, ví dụ vật lý) được dựng local theo mốc giọng đọc, không cần API hình ảnh trả phí. Biểu đồ là mô phỏng, không thay thế dữ liệu thị trường thật.
- Render MP4 dọc 1080×1920 với trạng thái job thực.
- Text overlay Finance Editorial mặc định trên video: kicker lime, headline trắng, nền tối bán trong suốt; không hiện bảng chỉnh overlay ở bước Edit.
- QA trước khi tải video thành phẩm.
- Demo mode để kiểm tra giao diện mà không tiêu API credit.

Preset overlay được giữ nội bộ để render tự động. Người dùng chỉ cần chọn phong cách Edit rồi chờ MP4 hoàn tất.

## Yêu cầu hệ thống

- Node.js 20.9 trở lên và npm.
- Python 3.11 trở lên.
- FFmpeg và `ffprobe` có trong `PATH` để render/QA video.
- Windows PowerShell cho các lệnh minh họa bên dưới. macOS/Linux có thể dùng lệnh copy tương đương.

## Cài đặt và chạy

```powershell
git clone https://github.com/yanbi1069-cmd/brandflow-studio-v2.git
cd brandflow-studio-v2
npm install
python -m pip install -r local-agent/requirements.txt
Copy-Item .env.example .env.local
npm run dev:full
```

Truy cập:

- Frontend: `http://localhost:3000/multi-niche`
- Local agent health: `http://127.0.0.1:8765/api/health`

`npm run dev:full` chạy đồng thời Next.js và local agent. Dùng `npm run dev` nếu chỉ muốn xem frontend/Demo mode.

## Cấu hình `.env.local`

Không gửi API key qua chat và không commit `.env.local`. Tự tạo file trên máy bằng cách copy `.env.example`, sau đó điền các biến cần dùng:

| Biến | Mục đích | Bắt buộc |
|---|---|---|
| `APIFY_API_TOKEN` | Research dữ liệu nền tảng | Khi research live |
| `KYMA_API_KEY` | Research/rerank/viết kịch bản qua Kyma | Khi dùng AI live |
| `HEYGEN_API_KEY` | Tạo video HeyGen | Khi dùng HeyGen |
| `HEYGEN_VOICE_ID` | Voice HeyGen | Khi dùng HeyGen |
| `HEYGEN_AVATAR_ID` | Photo Avatar III | Khi dùng HeyGen |
| `PEXELS_API_KEY` | B-roll ưu tiên | Khi lấy B-roll live |
| `PIXABAY_API_KEY` | B-roll fallback | Không |

Các biến model Kyma trong `.env.example` có giá trị mặc định và có thể đổi mà không sửa code.

## Luồng sử dụng thực tế

1. Nhập/cập nhật API trong Settings hoặc `.env.local` trên máy cá nhân.
2. Research bằng keyword + niche hoặc link kênh đối thủ.
3. Chọn video và đưa vào hàng đợi.
4. Tạo ba kịch bản, chọn và duyệt một bản.
5. Tạo HeyGen video, chọn no-face hoặc upload video gốc.
6. Chờ source video hoàn tất.
7. Chọn style edit; B-roll và text overlay được tự động ghép theo mốc audio thực tế.
8. Render video, kiểm tra QA và tải MP4.

Các thao tác HeyGen và API live có thể phát sinh chi phí. Chỉ bấm chạy sau khi chủ tài khoản xác nhận.

## Kiểm thử

```powershell
npm test
npm run build
python -m unittest discover -s local-agent/tests -v
python -m unittest discover -s engine/tests -v
python -m py_compile local-agent/agent_core.py engine/scripts/stock_broll.py engine/scripts/technical_broll.py engine/scripts/compose_video.py
```

Hướng dẫn test thủ công đầy đủ: [docs/TEST_LOCAL_V2.md](docs/TEST_LOCAL_V2.md).

## Cấu trúc repository

```text
app/            Next.js UI và API proxy routes
config/         Domain packs, content formats, edit styles
docs/           Kiến trúc, spec, test và onboarding
engine/         Pipeline dựng video, caption, B-roll và compose
lib/            Domain/script engine và local-agent client
local-agent/    HTTP agent, job state, HeyGen và workspace local
tests/          Node contract/regression tests
```

## Bảo mật và dữ liệu sinh ra

- `.env*` bị ignore, ngoại trừ file mẫu `.env.example`.
- `node_modules`, `.next`, `.vercel`, cache Python và log không được commit.
- `local-agent/workspace`, workspace job và mọi video/audio render được giữ local.
- Proxy server giữ credential khỏi bundle frontend.
- Không deploy Vercel từ quy trình phát hành source này.

## Tài liệu

- [Test local V2](docs/TEST_LOCAL_V2.md)
- [Onboarding Codex/Claude](docs/ONBOARDING-CODEX-CLAUDE.md)
- [Kiến trúc](docs/ARCHITECTURE.md)
- [Đặc tả](docs/SPEC.md)
- [Production engine](engine/PRODUCTION.md)
