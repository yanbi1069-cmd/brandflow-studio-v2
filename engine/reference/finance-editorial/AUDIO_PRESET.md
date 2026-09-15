# Audio preset đã chốt

Áp dụng khi có nhạc nền. Voice vẫn là lớp quan trọng nhất.

- Voice: `volume=0.96`.
- Background music: `volume=0.05`; fade-in 0.8 giây, fade-out khoảng 1.6 giây.
- Duck nhạc dưới voice: `sidechaincompress=threshold=0.10:ratio=2.0:attack=25:release=220`.
- Whoosh chuyển cảnh: `0.62–0.72`.
- Impact chính: `0.88`.
- Ting xác nhận: `0.78–0.86`.
- UI pop khi nhãn/sơ đồ xuất hiện: `0.76–0.80`.
- Limiter cuối: `limit=0.90`, attack 5 ms, release 80 ms.

Khoảng 8–10 điểm SFX cho video 35–45 giây. Chỉ đặt tại điểm chuyển cảnh, xuất hiện nhãn, breakout hoặc confirmation; không đặt giữa câu đang nói.

Nhạc `Crypto Corporate` của Stock-Waves chỉ dùng khi kiểm tra điều kiện license và thêm credit theo `docs/MUSIC_CREDIT.md`. Không coi file/mẫu nhạc trong project là quyền cấp phép để phân phối lại.

