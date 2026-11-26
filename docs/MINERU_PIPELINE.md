# Pipeline MinerU — Scanofy

## Phạm vi đã hoàn thiện

Pipeline hiện hỗ trợ output của `mineru-kit` **4.2.3**: `middle_json.json`
(schema `docvortex.middle` 2.0, có `pages[]`) và `markdown.md`.
PDF số/DOCX được router chọn MinerU. Scan/ảnh theo nhánh OCR khác hiện vẫn
`awaiting_ocr`; PaddleOCR, Chandra và Vintern thuộc giai đoạn tiếp theo.

1. Upload kiểm tra định dạng/dung lượng, lưu file gốc và tạo document/job.
2. API trả document; Workspace mở file gốc trong khi background task xử lý.
3. Profiler đo tài liệu, router chọn engine theo evidence.
4. Adapter chạy CLI, lưu ZIP/artifact ở thư mục riêng cho mỗi lần chạy.
5. Chọn chính xác artifact theo tên; từ chối thiếu, trùng, JSON lỗi hoặc page index lỗi.
6. Lưu raw output, Markdown, phiên bản CLI, SHA-256 file nguồn và manifest artifact.
7. Normalizer chuyển về contract Page–Block–Span; bổ sung kích thước trang đo từ nguồn.
8. Đối chiếu số trang PDF rồi lưu cấu trúc; cập nhật trạng thái `parsed`.

Khi lỗi, trạng thái phân tích là `failed`, có thông báo trong status/job;
file gốc vẫn đọc được. Retry tạo lần xử lý mới và giữ artifact của lần cũ.
Raw output được lưu trước bước chuẩn hóa để có thể khôi phục sau lỗi normalization.
Lỗi trước khi nhận được output hợp lệ không có snapshot raw mới trong database.

## Artifact và API

Artifact nằm tại `be/storage/mineru_outputs/<document_id>/<run_uuid>/`.
Metadata `_scanofy` trong raw output giữ đường dẫn tương đối cùng kích thước file.
Các ảnh và file bổ trợ trong ZIP được giữ lại; không yêu cầu phải có `layout.pdf`
hoặc `span.pdf`. Viewer vẽ overlay từ bbox chuẩn hóa trên tài liệu gốc.

- `GET /documents/{id}/pages`, `/blocks`, `/spans`: dữ liệu đã chuẩn hóa.
- `GET /documents/{id}/preview`: dữ liệu preview gắn parse run.
- `GET /documents/{id}/outputs/{output_id}/artifacts/{artifact_path}`:
  tải artifact nằm trong manifest của đúng document/output.

ZIP bị chặn path traversal và giới hạn 10.000 entry / 1 GiB giải nén.
API chỉ phục vụ file trong manifest và trong thư mục tài liệu; các loại ngoài
PDF/ảnh an toàn được tải dưới dạng attachment.

## Chuẩn hóa lại dữ liệu đã lưu

Chạy tại `be`, với đúng môi trường/database dự định thao tác:

```powershell
# Mặc định chỉ kiểm tra, đếm cấu trúc; không ghi dữ liệu.
.\.venv\Scripts\python.exe -m app.commands.renormalize --document-id <ID>

# Áp dụng cấu trúc từ raw output đã lưu; không gọi lại MinerU.
.\.venv\Scripts\python.exe -m app.commands.renormalize --document-id <ID> --apply

# Có thể thêm --reprofile để đo lại file nguồn trước khi chuẩn hóa.
```

Lệnh từ chối tài liệu đang xử lý, output không hỗ trợ hoặc số trang không khớp.
Lưu lặp giữ ID theo vị trí trang/block/span khi cấu trúc không đổi. Khi engine
đổi thứ tự/tách gộp block, không xem ID theo vị trí là định danh ngữ nghĩa lâu dài.
Artifact MinerU cũ dạng `original_middle.json`/`original_content_list_v2.json`
chưa được nhập bằng lệnh này: cần parse lại bằng phiên bản đang hỗ trợ.
Chưa chạy backfill tự động trên tài liệu người dùng.

## Kiểm chứng

```powershell
cd be
.\.venv\Scripts\python.exe -m pytest
# Opt-in: gọi MinerU thật, cần CLI/model đã cài.
.\.venv\Scripts\python.exe -m tests.live_mineru_smoke
```

Smoke test dùng PDF tổng hợp một trang và database SQLite/storage riêng dưới
`tmp/mineru-smoke-<uuid>`, không dùng Neon. Nó chạy migration, mở HTTP server
cục bộ, upload, đọc file gốc trong khi xử lý, đợi parsed, kiểm tra page/block/span,
preview, artifact và chuẩn hóa lại giữ ID span. Server kiểm thử được dừng khi xong.

Lần kiểm chứng ngày 26/11/2026, MinerU 4.2.3: upload trả sau **0,047 giây**,
toàn bài kiểm tra **13,266 giây**, kết quả **1 page / 1 block / 1 span**.
Đây là smoke test tính thông suốt, chưa phải benchmark độ chính xác hoặc tốc độ
trên PDF dài, tiếng Việt, bảng, công thức, scan và trang xoay/CropBox.
Fixture `be/tests/fixtures/mineru_v4_smoke_middle.json` lấy từ lần chạy thật này,
chỉ chứa nội dung tổng hợp, dùng kiểm thử hồi quy không gọi model.

## Sơ đồ dùng trong báo cáo

- [Mermaid có thể sửa](diagrams/mineru-pipeline.mmd)
- [SVG vector](diagrams/mineru-pipeline.svg)
- [PNG](diagrams/mineru-pipeline.png)

Gợi ý chú thích: **Hình — Luồng xử lý tài liệu bằng MinerU trong Scanofy:
đọc tài liệu gốc song song với phân tích và chuẩn hóa về Page–Block–Span.**

Mermaid mô tả cả retry/backfill. SVG/PNG tập trung luồng chính và chú thích các
nhánh phụ. Chạy `python scripts/render-mineru-diagram.py` từ gốc repo để tạo lại
SVG/PNG trên Windows có font Arial; thay đổi Mermaid cần cập nhật renderer tương ứng.

Hiện background task chạy trong tiến trình FastAPI, chưa có durable queue hay tự
khôi phục job khi server dừng. Đây là việc cần làm trước khi triển khai production.
