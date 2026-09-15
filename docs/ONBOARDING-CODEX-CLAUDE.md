# Onboarding Codex và Claude

Tài liệu này giúp một coding agent tiếp tục BrandFlow Studio V2 mà không cần đọc lại toàn bộ lịch sử dự án.

## Mục tiêu sản phẩm

Hoàn thiện agent tạo video thương hiệu cá nhân đa ngành theo luồng:

`Research → Script → Source Video → Edit → Final`

Ưu tiên là độ tin cậy của luồng local, bảo mật API key, chất lượng video dọc và khả năng tái tạo style Finance Editorial cho nhiều ngành.

## Đọc trước khi sửa

1. `AGENTS.md` — chỉ dẫn repository cho Codex và phiên bản Next.js hiện dùng.
2. `CLAUDE.md` — entry point cho Claude, hiện kế thừa `AGENTS.md`.
3. `README.md` — setup, tính năng và giới hạn vận hành.
4. `docs/ARCHITECTURE.md` và `docs/SPEC.md` — kiến trúc/contract sản phẩm.
5. `docs/TEST_LOCAL_V2.md` — regression và checklist E2E.
6. `engine/reference/finance-editorial/` — baseline trực tiếp cho overlay/edit.

Codex nên tuân thủ `AGENTS.md`; hướng dẫn chính thức OpenAI cũng lưu ý model có thể chịu ảnh hưởng mạnh từ file chỉ dẫn repository, vì vậy cần đọc và rà xung đột trước khi thay đổi: <https://developers.openai.com/api/docs/guides/latest-model>.

## Bản đồ code

| Khu vực | Trách nhiệm |
|---|---|
| `app/multi-niche/` | UI workflow và cấu hình Finance Editorial overlay |
| `app/api/local-agent/` | Proxy server-side tới local agent, không lộ key trên frontend |
| `lib/local-agent-client.js` | Client/contract giao tiếp local agent |
| `local-agent/app.py` | HTTP routes và media/job endpoints |
| `local-agent/agent_core.py` | Research, Kyma fallback, HeyGen, edit orchestration và job state |
| `engine/scripts/compose_video.py` | FFmpeg compose, overlay, layout và render MP4 |
| `engine/scripts/generate_captions.py` | Sinh caption |
| `config/` | Domain packs, content format và edit style preset |
| `tests/` | Node regression/compatibility tests |

## Contract cần giữ

- Frontend chính: `http://localhost:3000/multi-niche`.
- Local health: `http://127.0.0.1:8765/api/health`.
- Output video: MP4 dọc 1080×1920.
- Research trả về kênh, URL và các chỉ số công khai; không bịa dữ liệu thiếu.
- Script generation trả về ba phương án từ video đã duyệt.
- HeyGen dùng Photo Avatar III theo flow hiện tại.
- Pexels là nguồn B-roll ưu tiên; Pixabay là fallback tùy chọn.
- UI hiển thị `Đang edit…` trong thời gian render.
- Overlay không che mặt/phụ đề và giữ toàn bộ tùy chọn hiện có.
- API key chỉ ở `.env.local`/Settings local và server-side proxy.

## Quy tắc an toàn

- Không yêu cầu người dùng gửi API key qua chat.
- Không đọc/in nội dung `.env.local` vào transcript hoặc log.
- Không commit `.env.local`, token, workspace, media render, `.next` hoặc `node_modules`.
- Không gọi API tốn phí nếu chưa có xác nhận rõ ràng.
- Không tự deploy Vercel hoặc xuất bản video.
- Không xóa artifact local của người dùng khi dọn Git.
- Giữ thay đổi ngoài phạm vi; kiểm tra `git status` trước và sau khi sửa.

## Thiết lập phiên làm việc mới

```powershell
npm install
python -m pip install -r local-agent/requirements.txt
Copy-Item .env.example .env.local
npm run dev:full
```

Người vận hành tự điền vào `.env.local`:

```dotenv
APIFY_API_TOKEN=
KYMA_API_KEY=
HEYGEN_API_KEY=
HEYGEN_VOICE_ID=
HEYGEN_AVATAR_ID=
PEXELS_API_KEY=
PIXABAY_API_KEY=
```

`PIXABAY_API_KEY` là tùy chọn. Không thay key trống bằng dữ liệu giả có hình thức giống secret thật.

## Quy trình sửa đổi

1. Đọc trạng thái Git và file chỉ dẫn.
2. Xác định contract bị ảnh hưởng giữa UI → proxy → local agent → compose.
3. Thay đổi nhỏ nhất có thể, giữ backward compatibility cho manifest/job cũ.
4. Chạy test không tốn phí trước.
5. Chỉ chạy E2E live khi được xác nhận.
6. Kiểm tra video bằng `ffprobe` và QA hình ảnh nếu có thay đổi compose.
7. Quét staging để loại secret/generated media trước commit.

## Test bắt buộc trước bàn giao

```powershell
npm test
npm run build
python -m unittest discover -s local-agent/tests -v
python -m py_compile local-agent/agent_core.py engine/scripts/compose_video.py
```

Nếu thay đổi render, test thêm sample local không tốn API hoặc dùng artifact do người dùng cung cấp. Không commit output video.

## Prompt bàn giao mẫu

```text
Tiếp tục BrandFlow Studio V2 trong repository hiện tại.
Đọc AGENTS.md, README.md, docs/ONBOARDING-CODEX-CLAUDE.md và docs/TEST_LOCAL_V2.md trước khi sửa.
Giữ contract Research → Script → Source Video → Edit → Final.
Không đọc/in/commit secret hoặc generated media. Không gọi API tốn phí và không deploy nếu chưa được phép.
Kiểm tra git status, thực hiện thay đổi trong phạm vi, chạy test phù hợp và báo rõ file đã sửa.
```

