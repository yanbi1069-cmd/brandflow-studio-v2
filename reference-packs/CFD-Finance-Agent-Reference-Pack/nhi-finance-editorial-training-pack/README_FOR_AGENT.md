# Finance Editorial Training Pack — chị Nhi

Đây là bộ mẫu để học cách dựng một video Finance/Forex dọc theo phong cách **editorial motion graphic** đã được duyệt nội bộ. Đây là workflow edit từ footage có voice sẵn, không phải quy trình render avatar HeyGen.

## File quan trọng

- `source/finance_reference_raw.mp4`: footage gốc gồm talking-head và voice thật.
- `reference/finance_editorial_v12.mp4`: bản tham chiếu cuối đã duyệt về nhịp hình, âm thanh và không có flash frame.
- `scripts/build_reference.py`: mã tạo motion graphic, B-roll và subtitle của bản visual nền.
- `docs/STORYBOARD.md`: bản đồ từng beat hình theo lời thoại.
- `docs/DESIGN_SYSTEM.md`: visual grammar, màu, typography và nguyên tắc chuyển cảnh.
- `docs/AUDIO_PRESET.md`: mức mix đã chốt.
- `assets/broll/pexels_ebook.mp4`: B-roll thực tế từng dùng; xem `docs/MEDIA_MANIFEST.json` để biết nguồn/licensing.

## Cách agent phải làm

1. Nghe voice trước, tách các beat theo ý nghĩa; tuyệt đối không chia B-roll theo một số giây cố định.
2. Hook và CTA dùng full-screen talking-head. Phần giải thích kỹ thuật dùng full-screen motion graphic, không đặt B-roll ở nửa màn hình.
3. Mỗi scene kỹ thuật cần một “proof” nhìn được: ví dụ đường giá, vùng hỗ trợ, cấu trúc bị phá hoặc điều kiện BUY. Giữ proof trên màn hình đủ lâu để đọc, tối thiểu khoảng 0.9 giây.
4. Dùng B-roll đời sống/stock chỉ cho bối cảnh; không để B-roll thay thế lời giải thích kỹ thuật.
5. Các layer B-roll nối phải sát nhau hoặc có chủ đích chuyển sang avatar. Không tạo clip/overlay quá ngắn gây chớp khung hình.
6. Subtitle bám đúng voice, ưu tiên ngắt ở dấu phẩy/dấu chấm; tối đa 2 dòng và tránh tràn viền.
7. Trước khi bàn giao, kiểm tra toàn bộ điểm cut, các frame chuyển cảnh, subtitle dài và mix âm thanh.

## Không sao chép máy móc

Sao chép **logic** (voice → claim → visual proof) và hệ visual, không tái sử dụng nguyên chart, ảnh, footage hay CTA cho chủ đề khác. B-roll đời sống phải thay đổi theo video và tránh dùng hình người thật của đối thủ/cùng ngành.

## Chạy lại bản visual nền

Yêu cầu: Python, Pillow, FFmpeg, font Montserrat ExtraBold/SemiBold. Chạy từ thư mục pack:

```powershell
python scripts\build_reference.py
```

Script tái tạo bản visual V2 (không có mix SFX/BGM V12). Dùng `reference/finance_editorial_v12.mp4` để đối chiếu bản âm thanh hoàn chỉnh.

