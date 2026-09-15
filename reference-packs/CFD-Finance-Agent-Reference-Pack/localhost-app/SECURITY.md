# Security

- Server mặc định chỉ bind `127.0.0.1`; không mở ra LAN/Internet.
- Muốn bind remote phải chủ động đặt `CFD_AGENT_ALLOW_REMOTE=1` và tự chịu trách nhiệm thêm xác thực, TLS, firewall.
- Secret lưu trong `.env`, không trả lại qua API và không nằm trong artifact project.
- Mọi POST yêu cầu header `X-CFD-Agent: 1` và cùng origin; ứng dụng không bật CORS.
- HeyGen render và publishing là hành động tốn phí/thay đổi bên ngoài nên bắt buộc xác nhận ngay khi chạy.
- Upload giới hạn 1 GB, tên file được chuẩn hóa và đường dẫn bị giới hạn trong thư mục project.

