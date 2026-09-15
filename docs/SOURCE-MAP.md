# Source map and synthesis decisions

| Nguồn | Phần được kế thừa | Cách BrandFlow chuẩn hoá |
|---|---|---|
| Bài tập Build To Own Buổi 2–5 | Spec, architecture, research-first, test/deploy checklist | Đóng thành một sản phẩm duy nhất có demo mode và Definition of Done rõ ràng |
| `personal-brand-video-agent` trong project hiện tại | Module research → script → generator → editor, Kyma adapter | Hợp nhất thành một studio thay vì bốn CLI tách rời |
| `CFD-Finance-Agent-Reference-Pack` từ Agent thực chiến | Toàn bộ ProjectStore/JobManager, research table, 3 scripts + analysis/claim check, HeyGen, no-face, upload, edit handoff, feedback, QA và publishing | Giữ nguyên baseline Finance trong `reference-packs/`; tạo bản chạy đa ngành trong `local-agent/` bằng domain pack, không mang theo secret |
| Agent gốc | FastAPI job model, Remotion/FFmpeg pipeline, research breakout ratio | Giữ tư duy job + manifest; không bê cấu hình tài chính cá nhân hardcode |
| `mkt-skills` và `finance-editorial-edit` | Edit theo semantic beat, technical proof, subtitle safe-area, no flash | Chuyển thành Style Engine + bốn invariant QA dùng được cho nhiều ngành |

## Quyết định quan trọng

- `Editorial Proof` là style Finance mặc định; mỗi domain có default style riêng và người dùng có thể chọn một trong 18 style.
- B-roll thật chỉ là bổ trợ; claim kỹ thuật cần visual proof.
- Demo mode phải trung thực: tạo manifest và preview, không gọi đó là video đã render.
- Production giữ human-in-the-loop trước mọi bước tốn credit hoặc xuất bản.
