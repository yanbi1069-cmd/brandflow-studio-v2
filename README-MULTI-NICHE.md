# Personal Brand Video Agent V2

Đây là bản mở rộng đa ngành từ toàn bộ CFD Finance Agent hoàn chỉnh. Workflow Finance, persistence/job, ba source route, feedback versioning, QA và publishing gate được giữ nguyên; domain pack và multi-style editor là hai lớp mở rộng.

Chạy `npm run dev`, sau đó mở `http://localhost:3000/multi-niche`. Production runner đầy đủ nằm trong `local-agent/` và chạy bằng `python start_agent.py`.

B-roll đời sống dùng footage sở hữu trước, sau đó Pexels và Pixabay. Chạy `engine/scripts/stock_broll.py` để chuẩn bị các beat context, tải clip về job và tạo `media_manifest.json`; visual proof quan trọng vẫn được thiết kế riêng theo ngành.

Xem [docs/FINANCE-COMPATIBILITY-MATRIX.md](docs/FINANCE-COMPATIBILITY-MATRIX.md), [docs/FULL-SYSTEM.md](docs/FULL-SYSTEM.md) và [docs/MULTI-NICHE-SYSTEM.md](docs/MULTI-NICHE-SYSTEM.md). Hai skill cấp project nằm trong `../.Codex/skills/`.

Kiểm thử nhanh:

```powershell
npm test
npm run build
python engine/run_pipeline_v2.py tests/sample-manifest-v2.json --validate-only
python -m unittest discover -s local-agent/tests -p "test_*.py" -v
```
