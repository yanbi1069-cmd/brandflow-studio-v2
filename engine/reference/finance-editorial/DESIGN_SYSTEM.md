# Design — Editorial Multi-Timeframe Test

## Script fingerprint

- Topic: phân tích đa khung thời gian trong Forex.
- Audience: trader mới, thường vào lệnh ở M5 mà bỏ qua xu hướng lớn.
- Core tension: tín hiệu khung nhỏ nhìn có vẻ đẹp nhưng đi ngược khung lớn.
- Emotional temperature: cảnh báo, rõ ràng, thực dụng.
- Reality level: hybrid — talking-head thật + giao diện chart/infographic.
- Physical nouns: khung thời gian, đường giá, vùng hỗ trợ, lệnh BUY, điểm vào.
- Visual verbs: quét, thu nhỏ góc nhìn, đi xuống theo tầng, điều chỉnh, phá cấu trúc, xác nhận.
- Proof: đường giá 4H, vùng hỗ trợ và cú phá cấu trúc giảm trên khung nhỏ.

## Ba route đã cân nhắc

1. **Trading control room** — dashboard dày và nhiều panel. Loại vì dễ thành UI nhỏ, khó đọc trên điện thoại.
2. **Timeframe elevator** — đi dọc từ D1/H4 xuống H1 rồi M15/M5. Chọn vì trục dọc 9:16 biến đúng logic “khung lớn xuống khung nhỏ” thành chuyển động nhìn thấy được.
3. **Nested chart tunnel** — zoom từ chart lớn vào chart nhỏ. Loại vì triển khai nhanh dễ thành zoom trang trí, proof không rõ bằng route thang thời gian.

## Visual grammar

- Grammar chính: diagrammatic world với một đường dẫn dọc xuyên suốt.
- Grammar phụ: documentary interface cho order ticket và chart.
- Persistent motif: đường tín hiệu xanh neon chạy từ khung lớn xuống khung nhỏ.
- Palette: navy đen `#060B16`, trắng ngà `#F4F7EF`, xanh neon `#B6FF36`, đỏ cảnh báo `#FF4D5E`, vàng `#FFC857`.
- Typography: Montserrat ExtraBold/SemiBold, headline 72–92px, nội dung thiết yếu nằm trên vùng caption.
- Transition: clean cut và shared vertical trace; không dùng flash lặp lại.

## Test adaptation

Đây là bản thử nội bộ từ footage người thật đã có. Không gọi HeyGen, ElevenLabs, Pexels hay API trả phí. Hook và CTA giữ talking-head full-screen; phần giải thích giữa dùng motion graphic toàn màn hình. Audio gốc là timeline duy nhất.
