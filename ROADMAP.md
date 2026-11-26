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
- [x] Đã có artifact MinerU thực tế trong `be/storage/mineru_outputs`.

### Chưa hoàn thiện

- [x] Git monorepo Scanofy đã quản lý `fe`, `be`, `ai` và tài liệu ở thư mục gốc.
- [x] Python 3.11 và các direct dependency đã được chốt phiên bản.
- [x] MinerU 4.2.3 chạy qua `mineru-kit` trong `be/.venv`.
- [x] Docker Compose, backend và README cùng dùng `be/.env`.
- [x] File Profiler v1 đo PDF page/text/image evidence, ảnh và DOCX; chữ viết tay chưa biết giữ null.
- [x] MinerU 4 normalizer giữ Page/Block/Span và bbox 0–1 hợp lệ.
- [ ] Chandra adapter mới là placeholder.
- [x] PaddleOCR CPU adapter cho ảnh/PDF scan đã chạy thật; Vintern adapter còn chờ tuần 3.
- [x] Đã có backend unit/API tests và script kiểm tra toàn dự án.
- [x] Có PDF.js viewer cuộn liên tục, block overlay và mục lục heading.
- [ ] Hierarchy tree có quan hệ cha–con chưa triển khai.
- [ ] Chưa có benchmark dataset và evaluation harness.

## 4. Checklist trước khi phát triển tính năng mới

### 4.1. Bảo toàn mã nguồn

- [x] Kiểm tra toàn bộ thay đổi hiện tại của frontend.
- [x] Khởi tạo Git repository **Scanofy** tại workspace hiện tại để quản lý monorepo.
- [x] Bảo toàn lịch sử frontend trong nhánh `frontend-original` và Git bundle cục bộ.
- [x] Tạo `.gitignore` chung cho `.env`, `.venv`, `node_modules`, `.next`,
  database cục bộ, uploads, OCR outputs và cache.
- [x] Kiểm tra không có API key, mật khẩu database hoặc tài liệu riêng tư trong
  commit.
- [x] Tạo baseline commit `b3f4083` trước khi refactor.

### 4.2. Chuẩn hóa môi trường

- [x] Chọn Python 3.11 làm phiên bản chính thức cho backend trong `be`.
- [x] Tạo lại `be/.venv` từ `requirements-dev.txt`.
- [x] Đồng bộ phiên bản FastAPI trong requirements và virtualenv.
- [x] Chốt `be/.env` và cập nhật README/Docker Compose.
- [x] Kiểm tra kết nối PostgreSQL/Neon.
- [x] Chạy `alembic upgrade head` thành công (`202606270001`, head).
- [x] Cài MinerU 4.2.3 và chạy được local CLI `mineru-kit parse`.
- [x] Chạy frontend trong `fe`: lint và production build.
- [x] Chạy backend trong `be`: health check và OpenAPI qua ASGI smoke test.

### 4.3. Chốt data contract

- [x] Chốt `Page` schema: page number, width, height, source image; rotation nullable, chưa biết giữ null.
- [x] Chốt `Block` schema: canonical type, text, bbox, reading order, confidence, engine; giữ loại gốc trong raw_json.
- [x] Bổ sung `Span` model/schema, quan hệ với block và API lọc theo trang/block.
- [x] Thêm cờ `is_handwritten`, `needs_review` và `quality_score`; không tự suy đoán điểm/chữ viết tay khi thiếu dữ liệu.
- [x] Quy định hệ tọa độ bbox và cách scale lên PDF.js viewer; benchmark rotation/CropBox thực hiện sau.
- [x] Quy định mapping block type giữa MinerU, PaddleOCR, Chandra và Vintern; adapter/kiểm chứng ba engine sau vẫn thuộc tuần 3.
- [x] Tạo JSON Schema và fixture chuẩn dùng chung tại `shared/contracts` cho `be`, `fe` và `ai`.

### 4.4. Thiết lập kiểm thử

- [x] Backend unit test cho File Profiler, Router và Normalizer hiện tại.
- [x] API smoke test cho upload, status, pages, blocks và cleanup khi lỗi.
- [x] Fixture MinerU 4.2.3 từ PDF tổng hợp đã chạy CLI thật để test không cần model.
- [ ] Frontend test tối thiểu cho API client và trạng thái upload.
- [x] Có `scripts/check.ps1` chạy backend tests, frontend lint và build.

## 5. Timeline 8 tuần

## Tuần 1 - Nền tảng có thể tái lập

**Mục tiêu:** dựng lại và chạy dự án ổn định trên máy mới.

- [x] Hoàn thành toàn bộ checklist bảo toàn mã nguồn.
- [ ] Hoàn thành chuẩn hóa môi trường `fe`/`be`/`ai`.
- [x] Sửa cấu hình `.env` và Docker Compose.
- [x] Xác nhận migration và database schema trên Neon.
- [x] Hoàn thiện xử lý lỗi upload và cleanup file khi database lỗi.
- [x] Bổ sung test nền tảng.
- [x] Cập nhật hướng dẫn chạy dự án.

**Definition of Done:** clone/cài đặt/chạy được `fe` và `be`; upload file và
theo dõi trạng thái thành công.

## Tuần 2 - File Profiler và MinerU Normalizer

**Mục tiêu:** biến artifact MinerU thành page/block/span thật trong database.

- [x] Phân tích PDF text layer, page count và scan score dựa trên trang có ảnh/thiếu text; heuristic và giới hạn ghi ở `docs/FILE_PROFILER.md`.
- [x] Chọn rõ artifact MinerU theo tên thay vì lấy JSON đầu tiên; lỗi nếu thiếu/trùng/hỏng.
- [x] Parse `middle_json.json` của MinerU 4.2.3 (thay cho tên `original_middle.json` ở kế hoạch cũ).
- [x] Chốt nguồn cấu trúc là middle JSON có `pages[]`; không cần `original_content_list_v2.json` của bản cũ. Legacy import chưa hỗ trợ.
- [x] Chuẩn hóa page, block, span, bbox, reading order và block type.
- [x] Lưu Markdown, ảnh và manifest artifact theo từng lần chạy; có API tải artifact.
- [x] Chuẩn hóa lại Page/Block không tạo dữ liệu trùng, giữ ID theo vị trí trang/reading order; test lặp đã qua.
- [x] Thêm API trả page/block/span theo trang.
- [x] Viết test từ artifact MinerU 4.2.3 thực tế của PDF tổng hợp; có lệnh renormalize dry-run/apply và smoke test CLI thật.

Kiểm chứng pipeline một PDF tổng hợp đã qua; xem `docs/MINERU_PIPELINE.md`
và `docs/diagrams/`. Chưa thay thế benchmark tài liệu dài/tiếng Việt/bảng/công thức
ở tuần 5. Pipeline hiện dùng FastAPI background task, chưa có durable job queue.

**Definition of Done:** upload PDF -> MinerU -> database có đúng số trang và các
block có bbox; API trả dữ liệu đủ để vẽ overlay.

## Tuần 3 - Multi-engine OCR và chữ viết tay

**Mục tiêu:** định tuyến đúng tài liệu sang engine phù hợp.

- [x] Nền tảng Engine Registry/Orchestrator, execution plan và envelope chung; MinerU đi qua luồng chung. Xem `docs/ENGINE_ORCHESTRATION.md`.
- [x] Kiểm chứng engine giả có raw format riêng dùng chung persistence; giữ routing/API hiện có.
- [ ] Khái quát hóa artifact storage, thêm task theo trang/vùng, lịch sử attempts và worker/queue bền vững theo từng batch.
- [x] PaddleOCR adapter cho scan và ảnh văn bản in; worker CPU dùng cùng venv, chuẩn hóa dòng/bbox/confidence. Xem `docs/PADDLEOCR_PIPELINE.md`.
- [ ] Chandra adapter cho ảnh chữ viết tay/layout phức tạp.
- [ ] Vintern-1B adapter hoặc remote inference wrapper.
- [ ] Thêm lựa chọn upload: tự động, văn bản in, chữ viết tay, hỗn hợp.
- [ ] Tiền xử lý ảnh: rotate, perspective correction, deskew, contrast, denoise.
  Đã có EXIF và PDF native rotation/CropBox; perspective/deskew/contrast/denoise chưa triển khai.
- [ ] Router dùng profile thật và lựa chọn người dùng.
- [ ] Quality gate và fallback rule.
- [ ] Normalize output của mọi engine về cùng schema.
- [ ] Gắn `needs_review` cho kết quả bất đồng hoặc chất lượng thấp.

**Definition of Done:** PDF số, scan in và ảnh viết tay đều đi đúng nhánh; kết quả
đều trả page/block/bbox theo một schema.

## Tuần 4 - Interactive Document Viewer

**Mục tiêu:** xem trực quan kết quả OCR trên tài liệu gốc.

- [x] Render PDF bằng PDF.js; render ảnh trực tiếp cho image input.
- [x] Vẽ block overlay bằng HTML.
- [ ] Scale bbox chính xác khi zoom và resize.
- [ ] Bật/tắt layer theo block type.
- [ ] Chế độ span overlay dành cho debug/annotation.
- [x] Click block để xem text và metadata; bỏ native hover title theo yêu cầu UX.
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

1. [x] Thiết lập Git monorepo và baseline commit an toàn.
2. [x] Chuẩn hóa `.env`, Python virtualenv và MinerU CLI.
3. [ ] Chốt Page/Block/Span schema.
4. [ ] Viết fixture từ một output MinerU hiện có.
5. [x] Viết MinerU normalizer thật cho Page/Block và bbox chuẩn hóa.
6. [ ] Kiểm tra API page/block/span (Page/Block đã có; Span đang chờ schema).
7. [x] Làm viewer preview và layout overlay bản tối thiểu.

## 7. Quy tắc cập nhật checklist

- Chỉ đánh dấu hoàn thành khi đạt Definition of Done hoặc có test/chứng cứ chạy.
- Hạng mục đang làm vẫn giữ `- [ ]` và thêm hậu tố `(đang làm)`.
- Nếu thay đổi phạm vi, ghi quyết định vào mục 2 trước khi sửa timeline.
- Mỗi tuần ghi thêm một đoạn ngắn: đã làm, chưa làm, blocker và việc tuần sau.
- Không đưa khóa bí mật, thông tin cá nhân hoặc tài liệu benchmark có bản quyền vào
  repository công khai.

## 8. Nhật ký tiến độ

### Tuần hiện tại

- File Profiler v1: pypdf/Pillow đo trang, CropBox, rotation, text và image count; bỏ tỷ lệ giả định, giữ handwriting unknown. Router dùng bằng chứng đo, scan/ảnh chờ PaddleOCR, PDF hỗn hợp giữ MinerU. 40 backend tests đạt; hai PDF thật đo 17 và 12 trang, text ratio 1.0. Không tự cập nhật hồ sơ tài liệu cũ.

- Data contract v1: `docs/DATA_CONTRACT.md`; model/API Span và migration `202611260001` đã áp dụng. Span giữ nội dung, thứ tự, tham chiếu OCR output; geometry thiếu giữ null. Fixture tổng hợp tiếng Việt và test normalize lặp, cascade, API filters, migration lên/xuống đạt. Tài liệu cũ chưa backfill; text layer, version capture và rotation transforms vẫn đang chờ.

- Reader thumbnail panel: thay nút trước/sau bằng nút “Các trang”, ảnh thu nhỏ PDF tải gần viewport, chọn thumbnail cuộn tới trang; panel đóng/mở và đánh dấu trang hiện tại. Browser QA xác nhận mở, chọn trang 3 và đóng; console không có lỗi.

- Batch 2026-11-26: chốt luồng Library/upload/Workspace/retry/delete; 23 backend tests và frontend lint/build đạt. Sửa normalize lặp giữ Page/Block IDs, kiểm tra bbox hữu hạn 0–1, preview thêm parse_run_id và heading_level. Reader cuộn đến đúng block nguồn và chỉ bắt đầu render canvas gần viewport. Browser QA xác nhận heading trang 2 được highlight và đưa vào vùng nhìn; console không có lỗi.
- Chưa hoàn tất: Span model/API, PDF text layer, giải phóng canvas xa viewport, benchmark rotation/CropBox và kiểm thử upload end-to-end với MinerU thật trong lần chốt này.

- UX update 2026-11-25: Library là danh sách chính có tìm kiếm/lọc, upload thu gọn và kéo thả; upload lưu thành công mở thẳng Document Workspace. Workspace đọc file gốc khi đang phân tích hoặc lỗi, polling mở mục lục khi sẵn sàng; thêm retry API có kiểm tra trạng thái và giữ file gốc.

- Đã làm:
  - Khảo sát lại cấu trúc và trạng thái dự án.
  - Đọc và đối chiếu đề cương chính thức với roadmap cũ.
  - Chốt vai trò Chandra cho nhánh chữ viết tay.
  - Đổi tên sản phẩm và repository thành Scanofy.
  - Khởi tạo Git monorepo, bảo toàn lịch sử frontend và tạo baseline commit.
  - Chuẩn hóa ba thư mục chính của monorepo thành `fe`, `be`, `ai`.
  - Chốt Python 3.11, dependency backend và Node.js tối thiểu.
  - Thống nhất cấu hình backend tại `be/.env`; xác nhận migration Neon ở head.
  - Thêm backend tests, upload cleanup và script kiểm tra toàn dự án.
  - Chạy thành công backend tests, frontend lint và production build.
  - Cập nhật adapter cho MinerU 4.2.3 và xác minh PDF thật đi đến `parsed`.
  - Chốt `SCANOFY_DESIGN.md` theo hướng Calm Intelligence, lấy cảm hứng có chọn lọc từ Heptabase.
  - Xây design tokens, app shell và refactor màn Library thành các component dùng chung.
  - Kiểm tra trực quan Library ở desktop 1440×900 và mobile 390×844.
  - Chuẩn hóa output MinerU 4 thành Page/Block, giữ bbox `normalized_0_1` và nội dung span.
  - Thêm API phục vụ file gốc và preview; thêm proxy cùng origin ở frontend.
  - Xây Document Reader với PDF gốc, bản đồ layout, chọn block và chuyển trang.
  - Kiểm tra Reader với PDF thật gồm 12 trang và 128 block ở desktop/mobile.
  - Nâng Reader lên PDF.js canvas với overlay block trực tiếp và zoom/fit-width.
  - Thay panel block map bằng mục lục heading và chi tiết nguồn đang chọn.
  - Đồng bộ mục lục, trang PDF và block selection; giữ layout diagnostics trong disclosure.
  - Chuyển PDF viewer sang cuộn liên tục toàn bộ trang, tự cập nhật trang đang đọc và bỏ native hover title trên block.
- Đang làm:
  - Chốt data contract Span và phép biến đổi bbox theo rotation/CropBox.
- Blocker:
  - Chưa có text-layer/Span chuẩn để đồng bộ highlight trực tiếp trên PDF canvas.
  - `npm audit` phát hiện Next.js 16.2.9 có advisory nghiêm trọng; cần nâng framework ở batch bảo trì riêng.
- Tiếp theo:
  - Bổ sung Span schema/text layer và nâng Next.js lên bản vá an toàn sau khi chạy regression.
