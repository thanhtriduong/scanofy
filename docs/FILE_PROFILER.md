# File Profiler v1.0

Profiler inspects local input before engine routing. It performs no OCR, model inference or remote calls.

## Measured fields

- `size_bytes`: actual stored file size.
- PDF `page_count`: number of pages read by pypdf.
- PDF `pages[]`: 1-based page number, CropBox width/height in PDF points (UserUnit applied), declared rotation, extractable alphanumeric character count, presence of useful text, number of image resource keys and page classification.
- Image: verified image format/container and pixel width/height; not a handwriting or scan classifier.
- DOCX: text count from document.xml; pagination remains null because it depends on document layout/rendering. Text in headers/footers and drawings is not measured in v1.

## Heuristics, not confidence scores

Useful text means at least 20 Unicode alphanumeric characters extracted from a page. The threshold is recorded in the profile and requires calibration on a benchmark.
`text_layer_ratio` = useful-text pages / total pages.
`scan_score` = pages with at least one image resource and insufficient useful text / total pages.
A blank/vector-only page is not counted as a scan. Short title pages may be sparse; an image could be a photograph/logo rather than a scan. Image count is not painted area coverage. A scan with an existing OCR text layer can count as useful text.
If any page's text cannot be measured, aggregate ratios remain null, warnings record the limitation, and classification remains unknown. `handwriting_score` stays null for all automatic profiles.

PDF classes: digital_pdf (text pages, no scan candidates), scanned_pdf (scan candidates, no useful-text pages), mixed (both), sparse_or_blank, unknown.
Corrupt PDFs and password-protected PDFs requiring a password raise actionable errors; original file storage is retained.
Text extraction is skipped for decoded content streams above 10 MiB. Decoding itself can still consume memory; this is not a complete protection against hostile PDF decompression. Durable job isolation/resource limits remain future work.

## Routing

| Evidence | Target |
| --- | --- |
| Explicit handwriting signal >= 0.4 | Chandra |
| DOCX | MinerU |
| Mixed PDF | MinerU with page evidence retained |
| PDF useful-text ratio >= 0.6 | MinerU |
| Image input / scan_score >= 0.5 | PaddleOCR |
| Sparse/unknown PDF | MinerU parser |

Only MinerU currently runs in the processing service. Planned OCR targets remain awaiting_ocr until their adapters are implemented. Routing does not imply an engine has processed the file. Mixed documents are not split among engines in v1.

Measured PDF dimensions/rotation are persisted to normalized Page records after MinerU finishes. This does not change bbox orientation or prove CropBox alignment.
Existing documents are not automatically profiled again. Their saved legacy profiles can still contain placeholder ratios until reprocessing.

Libraries: pypdf 7.1.1 and Pillow 13.0.0, declared as backend runtime dependencies independently of MinerU.
