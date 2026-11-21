# Scanofy - Kế hoạch triển khai

Tài liệu này là checklist làm việc chung của dự án. Sau mỗi hạng mục hoàn thành,
đổi `- [ ]` thành `- [x]` và ghi ngắn gọn kết quả hoặc liên kết tới commit/PR.

## 1. Mục tiêu sản phẩm

Xây dựng hệ thống nhận dạng và tái cấu trúc tài liệu giáo dục tiếng Việt theo
pipeline:

```text
Tài liệu đầu vào
  -> File Profiler
  -> OCR/Parser Router
  -> MinerU / PaddleOCR / Chandra / Vintern-1B
  -> Unified Page-Block-Span Schema
  -> Vietnamese Post-correction
  -> Hierarchy Builder
  -> Interactive Document Workspace
  -> Tóm tắt / Dịch / Câu hỏi / Giải thích / Xuất tài liệu
```

Đầu ra quan trọng nhất:

- Nội dung OCR có thể truy vết về trang và bounding box gốc.
- Cây nội dung `Chương -> Mục -> Block` có thể điều hướng.
- Người dùng thao tác AI trên từng node và luôn thấy nguồn.
- Có benchmark định lượng bằng CER/WER và đánh giá cấu trúc cây.

## 2. Quyết định kỹ thuật đã thống nhất

- Benchmark chính thức theo đề cương: **PaddleOCR, MinerU, Vintern-1B**.
- Chandra là engine chuyên biệt cho **chữ viết tay và ảnh có layout phức tạp**.
- MinerU ưu tiên cho PDF/DOCX có text layer hoặc tài liệu số.
- PaddleOCR ưu tiên cho scan và ảnh văn bản in.
- Vintern-1B là fallback/đối chiếu cho tiếng Việt và kết quả chất lượng thấp.
- Chandra và Vintern có thể được so sánh riêng trên tập chữ viết tay.
- Mọi engine phải trả về cùng một schema page/block/span.
- Viewer web render tài liệu gốc và overlay bounding box từ JSON; không dùng
  `layout.pdf` hoặc `span.pdf` làm giao diện chính.
- Block overlay bật mặc định; span overlay chỉ bật khi debug/annotation.
- PostgreSQL lưu metadata/cấu trúc; file gốc và artifact OCR lưu ở object storage
  hoặc filesystem trong giai đoạn phát triển.

## 3. Trạng thái hiện tại

### Đã có

- [x] Frontend Next.js có upload, danh sách tài liệu và trạng thái xử lý.
- [x] Backend FastAPI có health check và API document cơ bản.
- [x] SQLAlchemy models cho document, job, OCR output, page, block, tree node,
  chunk và generated feature.
- [x] Alembic initial migration.
- [x] Upload file vào local storage với giới hạn dung lượng.
- [x] Background task placeholder cho pipeline xử lý.
- [x] MinerU CLI adapter cơ bản.
- [x] API đọc OCR output, pages và blocks.
- [x] Đã có artifact MinerU thực tế trong `backend/storage/mineru_outputs`.

### Chưa hoàn thiện

- [ ] Git chưa quản lý toàn bộ monorepo; backend hiện chưa nằm trong repository.
- [ ] Môi trường Python và `requirements.txt` chưa đồng bộ phiên bản.
- [ ] MinerU chưa khả dụng ổn định trên `PATH`.
- [ ] Docker Compose và vị trí `.env` chưa thống nhất.
- [ ] File Profiler vẫn dùng dữ liệu giả định.
- [ ] MinerU normalizer hiện gom toàn tài liệu thành một page và một block.
- [ ] Chandra adapter mới là placeholder.
- [ ] Chưa có PaddleOCR adapter và Vintern adapter.
- [ ] Chưa có automated tests thực tế.
- [ ] Chưa có document viewer, block overlay và hierarchy tree.
- [ ] Chưa có benchmark dataset và evaluation harness.

## 4. Checklist trước khi phát triển tính năng mới

### 4.1. Bảo toàn mã nguồn

- [ ] Kiểm tra toàn bộ thay đổi hiện tại của frontend.
- [ ] Khởi tạo Git repository **Scanofy** tại workspace hiện tại để quản lý monorepo.
- [ ] Không làm mất lịch sử Git hiện có của frontend khi chuyển thành monorepo.
- [ ] Tạo `.gitignore` chung cho `.env`, `.venv`, `node_modules`, `.next`,
  database cục bộ, uploads, OCR outputs và cache.
- [ ] Kiểm tra không có API key, mật khẩu database hoặc tài liệu riêng tư trong
  commit.
- [ ] Tạo baseline commit trước khi refactor.

### 4.2. Chuẩn hóa môi trường

- [ ] Chọn phiên bản Python chính thức cho backend.
- [ ] Tạo lại `backend/.venv` từ `requirements.txt`.
- [ ] Đồng bộ phiên bản FastAPI trong requirements và virtualenv.
- [ ] Chốt một vị trí `.env` duy nhất và cập nhật README/Docker Compose.
- [ ] Kiểm tra kết nối PostgreSQL/Neon.
- [ ] Chạy `alembic upgrade head` thành công.
- [ ] Cài MinerU trong môi trường riêng và chạy được `mineru --help`.
- [ ] Chạy frontend lint và production build.
- [ ] Chạy backend health check và OpenAPI.

### 4.3. Chốt data contract

- [ ] Chốt `Page` schema: page number, width, height, source image.
- [ ] Chốt `Block` schema: type, text, bbox, reading order, confidence, engine.
- [ ] Bổ sung `Span` model/schema và quan hệ với block.
- [ ] Thêm cờ `is_handwritten`, `needs_review` và `quality_score`.
- [ ] Quy định hệ tọa độ bbox và cách scale lên PDF.js viewer.
- [ ] Quy định mapping block type giữa MinerU, PaddleOCR, Chandra và Vintern.
- [ ] Tạo fixture JSON chuẩn dùng chung cho backend và frontend.

### 4.4. Thiết lập kiểm thử

- [ ] Backend unit test cho File Profiler, Router và Normalizer.
- [ ] API smoke test cho upload, status, pages và blocks.
- [ ] Fixture MinerU nhỏ để test mà không chạy model thật.
- [ ] Frontend test tối thiểu cho API client và trạng thái upload.
- [ ] Một lệnh hoặc script chạy toàn bộ lint/test.

## 5. Timeline 8 tuần

## Tuần 1 - Nền tảng có thể tái lập

**Mục tiêu:** dựng lại và chạy dự án ổn định trên máy mới.

- [ ] Hoàn thành toàn bộ checklist bảo toàn mã nguồn.
- [ ] Hoàn thành chuẩn hóa môi trường frontend/backend.
- [ ] Sửa cấu hình `.env` và Docker Compose.
- [ ] Xác nhận migration và database schema.
- [ ] Hoàn thiện xử lý lỗi upload và cleanup file khi database lỗi.
- [ ] Bổ sung test nền tảng.
- [ ] Cập nhật hướng dẫn chạy dự án.

**Definition of Done:** clone/cài đặt/chạy được frontend và backend; upload file và
theo dõi trạng thái thành công.

## Tuần 2 - File Profiler và MinerU Normalizer

**Mục tiêu:** biến artifact MinerU thành page/block/span thật trong database.

- [ ] Phân tích PDF text layer, page count và scan score thật.
- [ ] Chọn rõ artifact MinerU theo tên thay vì lấy JSON đầu tiên.
- [ ] Parse `original_middle.json`.
- [ ] Parse `original_content_list_v2.json`.
- [ ] Chuẩn hóa page, block, span, bbox, reading order và block type.
- [ ] Lưu Markdown, ảnh và tham chiếu artifact cần thiết.
- [ ] Làm pipeline idempotent để rerun không tạo dữ liệu trùng.
- [ ] Thêm API trả page/block/span theo trang.
- [ ] Viết test từ artifact MinerU hiện có.

**Definition of Done:** upload PDF -> MinerU -> database có đúng số trang và các
block có bbox; API trả dữ liệu đủ để vẽ overlay.

## Tuần 3 - Multi-engine OCR và chữ viết tay

**Mục tiêu:** định tuyến đúng tài liệu sang engine phù hợp.

- [ ] PaddleOCR adapter cho scan và ảnh văn bản in.
- [ ] Chandra adapter cho ảnh chữ viết tay/layout phức tạp.
- [ ] Vintern-1B adapter hoặc remote inference wrapper.
- [ ] Thêm lựa chọn upload: tự động, văn bản in, chữ viết tay, hỗn hợp.
- [ ] Tiền xử lý ảnh: rotate, perspective correction, deskew, contrast, denoise.
- [ ] Router dùng profile thật và lựa chọn người dùng.
- [ ] Quality gate và fallback rule.
- [ ] Normalize output của mọi engine về cùng schema.
- [ ] Gắn `needs_review` cho kết quả bất đồng hoặc chất lượng thấp.

**Definition of Done:** PDF số, scan in và ảnh viết tay đều đi đúng nhánh; kết quả
đều trả page/block/bbox theo một schema.

## Tuần 4 - Interactive Document Viewer

**Mục tiêu:** xem trực quan kết quả OCR trên tài liệu gốc.

- [ ] Render PDF bằng PDF.js; render ảnh trực tiếp cho image input.
- [ ] Vẽ block overlay bằng SVG/HTML.
- [ ] Scale bbox chính xác khi zoom và resize.
- [ ] Bật/tắt layer theo block type.
- [ ] Chế độ span overlay dành cho debug/annotation.
- [ ] Hover/click block để xem text và metadata.
- [ ] Danh sách block đồng bộ với trang đang xem.
- [ ] Cho phép sửa text và block type ở mức cơ bản.
- [ ] Tối ưu chỉ render overlay cho các trang đang nhìn thấy.

**Definition of Done:** người dùng chọn tài liệu, xem từng trang và click được mọi
block OCR tại đúng vị trí.

## Tuần 5 - Tiếng Việt và benchmark OCR

**Mục tiêu:** đo và cải thiện chất lượng OCR bằng số liệu.

- [ ] Chọn 20-50 trang pilot có ground truth.
- [ ] Xây annotation format cho text, bbox và block type.
- [ ] Cài CER/WER evaluation harness.
- [ ] Lưu raw text và corrected text riêng biệt.
- [ ] Vietnamese post-correction có giới hạn, không tự ý thay đổi nội dung.
- [ ] Báo cáo lỗi theo dấu tiếng Việt và loại tài liệu.
- [ ] So sánh PaddleOCR, MinerU và Vintern-1B.
- [ ] So sánh Chandra, Vintern và PaddleOCR trên tập chữ viết tay.
- [ ] Thu thập correction của người dùng làm ground truth có kiểm duyệt.

**Definition of Done:** có báo cáo CER/WER tái lập được và danh sách lỗi ưu tiên.

## Tuần 6 - Hierarchy Builder

**Mục tiêu:** chuyển chuỗi block thành cây nội dung.

- [ ] Phát hiện heading và heading level.
- [ ] Xây quan hệ tài liệu -> chương -> mục -> block.
- [ ] Mỗi node lưu block IDs, page range và order.
- [ ] API đọc cây và node detail.
- [ ] Tree viewer trên frontend.
- [ ] Click tree node để cuộn/highlight block nguồn.
- [ ] Cho phép chỉnh parent/level/title của node.
- [ ] Xây metric đánh giá hierarchy.

**Definition of Done:** tài liệu mẫu có cây điều hướng được và mọi node truy ngược
được về block/trang gốc.

## Tuần 7 - Interactive AI Workspace

**Mục tiêu:** thực hiện tác vụ AI trên node được chọn.

- [ ] Chunking theo node và giữ source block IDs.
- [ ] Tóm tắt node.
- [ ] Dịch node.
- [ ] Sinh câu hỏi trắc nghiệm.
- [ ] Sinh câu hỏi tự luận.
- [ ] Giải thích nội dung và công thức.
- [ ] Flashcards nếu phù hợp.
- [ ] Mọi kết quả hiển thị block/page nguồn.
- [ ] Lưu generated feature và lịch sử.
- [ ] Xuất nội dung đã chọn.

**Definition of Done:** chọn một node và chạy được ít nhất tóm tắt, câu hỏi và giải
thích với trích dẫn nguồn.

## Tuần 8 - Đánh giá, hoàn thiện và demo

**Mục tiêu:** tạo phiên bản có thể báo cáo và bảo vệ.

- [ ] Mở rộng benchmark hướng tới 500-1.000 trang.
- [ ] Hoàn thiện báo cáo CER/WER giữa ba engine chính.
- [ ] Báo cáo riêng cho chữ viết tay có Chandra.
- [ ] Đánh giá Hierarchy Builder.
- [ ] User testing cho viewer và AI workspace.
- [ ] Tối ưu latency, cache và xử lý job lỗi.
- [ ] Chuyển background task sang queue bền vững nếu triển khai production.
- [ ] Bảo mật CORS, upload, file access và API key.
- [ ] Docker/deployment.
- [ ] README kiến trúc và hướng dẫn sử dụng.
- [ ] Video demo, báo cáo và kịch bản thuyết trình.

**Definition of Done:** demo end-to-end, có benchmark và tài liệu chứng minh kết
quả theo đề cương.

## 6. Việc triển khai ngay tiếp theo

Không bắt đầu viewer hoặc AI feature trước khi dữ liệu bbox được chuẩn hóa đúng.
Thứ tự thực hiện gần nhất:

1. [ ] Thiết lập Git monorepo và baseline commit an toàn.
2. [ ] Chuẩn hóa `.env`, Python virtualenv và MinerU CLI.
3. [ ] Chốt Page/Block/Span schema.
4. [ ] Viết fixture từ một output MinerU hiện có.
5. [ ] Viết MinerU normalizer thật.
6. [ ] Kiểm tra API page/block/span.
7. [ ] Làm viewer overlay bản tối thiểu trên một trang.

## 7. Quy tắc cập nhật checklist

- Chỉ đánh dấu hoàn thành khi đạt Definition of Done hoặc có test/chứng cứ chạy.
- Hạng mục đang làm vẫn giữ `- [ ]` và thêm hậu tố `(đang làm)`.
- Nếu thay đổi phạm vi, ghi quyết định vào mục 2 trước khi sửa timeline.
- Mỗi tuần ghi thêm một đoạn ngắn: đã làm, chưa làm, blocker và việc tuần sau.
- Không đưa khóa bí mật, thông tin cá nhân hoặc tài liệu benchmark có bản quyền vào
  repository công khai.

## 8. Nhật ký tiến độ

### Tuần hiện tại

- Đã làm:
  - Khảo sát lại cấu trúc và trạng thái dự án.
  - Đọc và đối chiếu đề cương chính thức với roadmap cũ.
  - Chốt vai trò Chandra cho nhánh chữ viết tay.
- Đang làm:
  - Chuẩn bị baseline và môi trường để tiếp tục phát triển.
- Blocker:
  - MinerU chưa có trên `PATH` hiện tại.
  - Git chưa quản lý toàn bộ workspace.
  - Normalizer chưa giữ page/block/span/bbox thực tế.
- Tiếp theo:
  - Bắt đầu từ mục 1 trong phần "Việc triển khai ngay tiếp theo".
