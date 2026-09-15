# BrandFlow Studio — Product Spec v1.0

## Vấn đề

Chủ SME và chuyên gia Việt Nam đang ghép rời rạc nhiều công cụ để làm video thương hiệu cá nhân. Họ thiếu thời gian research, khó giữ giọng thương hiệu, và khâu hậu kỳ thường tạo ra video generic hoặc lộ chất AI.

## Người dùng chính

- Chủ doanh nghiệp nhỏ, chuyên gia, coach và đội marketing nhỏ.
- Đã có sản phẩm/dịch vụ thật nhưng chưa có editor chuyên trách.
- Cần đăng video đều, ưu tiên chất lượng và tính nhất quán hơn số lượng vô hạn.

## Giá trị khác biệt

1. Research theo tín hiệu breakout trước khi viết.
2. Kịch bản học cấu trúc nhưng không sao chép câu chữ.
3. Avatar/no-face là một lựa chọn trong cùng pipeline.
4. Edit là style engine có quy tắc, visual proof và QA, không phải bộ filter trang trí.
5. Mỗi video có manifest để tái tạo và sửa lại.

## Flow chính

1. Lưu Brand Memory: tên, ngách, khán giả, voice.
2. Research YouTube qua Apify hoặc dữ liệu demo.
3. Chọn một tín hiệu; tạo và duyệt kịch bản qua Kyma hoặc demo engine.
4. Chọn avatar/no-face và edit style.
5. Tạo production manifest; chuyển sang engine local để gọi HeyGen, align caption, dựng B-roll và render.
6. QA toàn bộ video; lưu job vào thư viện.

## Không làm trong v1

- Không tự chi tiền API khi người dùng chỉ xem demo.
- Không auto-post lên mạng xã hội.
- Không lưu key, token, avatar ID hoặc voice ID trong repository.
- Không giả vờ một manifest đã là video MP4 hoàn chỉnh.
- Không thay thế bước duyệt nội dung và QA của con người.

## Definition of Done

- Web app chạy local và build production thành công.
- Demo mode hoàn thành flow research → script → style → manifest không cần key.
- Live adapters cho Apify và Kyma chỉ chạy khi có biến môi trường.
- Manifest local được validator chấp nhận và sinh đúng cấu trúc job.
- Responsive ở mobile/desktop, có focus state, label và reduced-motion.
- Có tài liệu setup, source map, production workflow và checklist bài học.
