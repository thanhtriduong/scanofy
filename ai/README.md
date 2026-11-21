# Scanofy AI

`ai` là workspace dành cho các thành phần OCR, document intelligence và đánh
giá mô hình của Scanofy.

## Phạm vi

- Adapter cho MinerU, PaddleOCR, Chandra và Vintern-1B.
- File profiling và quyết định route OCR.
- Chuẩn hóa output về schema page/block/span dùng chung.
- Hậu xử lý tiếng Việt và quality gate.
- Benchmark CER/WER, layout và hierarchy.
- Fixtures và test dành riêng cho inference/evaluation.

## Ranh giới với các workspace khác

- `fe`: giao diện upload, document viewer, overlay và interactive workspace.
- `be`: API, database, job orchestration, storage và authentication.
- `ai`: inference, normalization, correction và evaluation.

Hiện tại các adapter OCR cũ vẫn nằm trong `be/app/services` để giữ pipeline đang
chạy. Chúng sẽ được tách dần sang `ai` sau khi data contract page/block/span được
chốt; không di chuyển hàng loạt trước khi có test bảo vệ.

