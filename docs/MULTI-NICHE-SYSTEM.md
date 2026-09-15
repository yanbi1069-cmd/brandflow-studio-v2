# BrandFlow Multi-Niche System

## Kiến trúc sản phẩm

BrandFlow v2 tách sản phẩm thành bốn lớp có thể thay độc lập:

1. Core pipeline giữ research, script, source video, edit, QA và distribution.
2. Domain pack quyết định audience, từ khóa research, loại bằng chứng, compliance và disclaimer.
3. Content format quyết định cấu trúc kể chuyện.
4. Edit preset quyết định nhịp dựng, caption, text effect, transition, easing và ưu tiên B-roll. Catalog hiện có 18 style, gồm 8 style HyperFrames đã xác minh từ upstream.

## Quy tắc video gốc và B-roll

Edit plan phân loại từng câu theo chức năng thay vì xen cảnh theo một khoảng thời gian cố định:

- `presenter`: giữ avatar/video gốc ở hook, quan điểm, đoạn chuyển và CTA.
- `proof`: dùng chart, tài liệu, screenshot, demo hoặc visual tự thiết kế.
- `context`: ưu tiên footage của thương hiệu, sau đó tìm Pexels và fallback Pixabay.
- `metaphor`: tự thiết kế một hình ảnh/đạo cụ khớp chính xác, không lấy stock trang trí.

Khi B-roll kết thúc mà ý giải thích vẫn tiếp tục, renderer quay lại video gốc. Nếu cả Pexels và Pixabay không có clip dọc phù hợp, dùng video gốc hoặc typography. Mọi stock asset được tải về job và ghi nguồn trong `media_manifest.json`.

Finance không còn bị hard-code vào core. Nó là domain pack tham chiếu có chart/calculation/official source và ràng buộc không cam kết lợi nhuận. Thêm ngành mới chỉ cần thêm một object vào `config/domain-packs.json` nếu pipeline không thay đổi.

## Những phần đã chuyển từ Finance reference pack

- Approval gates từ research tới publishing.
- Ba production route: AI avatar, no-face và source upload/raw footage.
- Voice-aligned edit, visual proof theo từng luận điểm, caption hai dòng, no-flash QA.
- Artifact contract, versioned feedback và mặc định Skip publishing.
- Finance Editorial trở thành preset `editorial-proof`, giữ rule chart/source rõ ràng.

## Những phần đã chọn lọc từ mkt-skills

- Format Observation–Action và Challenge–Reframe cho script nói tự nhiên.
- Jenga Tension, Visual Metaphor và Untold Story cho góc kể đa dạng.
- Raw creator edit: jump cut, word-highlight caption, punch zoom có kiểm soát.
- Screen demo/prompt typing, data kinetic, layered documentary reveal.
- Tách production planning khỏi render; preview và duyệt trước khi xuất final.

Các ý tưởng được chuẩn hóa lại thành schema BrandFlow thay vì sao chép toàn repo, để giảm phụ thuộc đường dẫn, API và asset riêng của tác giả nguồn.

## Chạy bản đa ngách

```powershell
npm run dev
```

Mở `http://localhost:3000/multi-niche`.

Tạo manifest trong UI, tải JSON rồi kiểm tra bằng:

```powershell
python engine/run_pipeline_v2.py path/to/manifest.json --validate-only
```

## Mở rộng một ngách mới

1. Thêm domain pack với ID ổn định.
2. Định nghĩa ít nhất ba proof type và hai compliance rule có tác động thật.
3. Chọn default edit style phù hợp asset mà khách hàng thực sự có.
4. Test ít nhất một kịch bản demo, một manifest và một edit brief.
5. Không đưa brand asset, credential hoặc case study riêng của khách vào catalog dùng chung.
