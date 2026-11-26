# Scanofy document contract v1.1

## Shared boundary (roadmap 4.3)

Canonical JSON Schema: `shared/contracts/normalized-document.schema.json`.
Canonical synthetic fixture: `shared/contracts/normalized-document.fixture.json`.
Pydantic implementation: `be/app/schemas/normalized.py`; tests reject schema drift.
Backend normalization validates this boundary before returning data. Frontend/AI can consume the shared JSON without importing engine fields.
Pages are unique, blocks reference existing pages and have unique reading order per page, spans have contiguous zero-based order.

Page dimensions and source image may be null if unavailable. Rotation is nullable, otherwise 0/90/180/270 degrees. This defines storage semantics; automatic measurement and transform benchmarking remain separate work.
Block `is_handwritten` is tri-state: true/false only when evidence exists, null means unknown. `quality_score` is nullable 0..1, not a substituted engine confidence. `needs_review` is boolean; the MinerU normalizer flags missing/invalid geometry and unknown block type. A false flag is not a quality guarantee.
Block coordinate system and heading level are now explicit persisted columns. Older rows remain nullable until re-normalization.

### Canonical block types and adapter mapping

Types: title, heading, paragraph, list, table, image, equation, caption, header, footer, page_number, footnote, reference, unknown.
Executable mapping: `be/app/services/block_types.py`. Original labels remain in `raw_json.type`.

| Engine | Example input aliases → canonical types | Status |
| --- | --- | --- |
| MinerU | doc_title → title; paragraph_title → heading; text → paragraph; ref_text → reference; page_footnote → footnote | Used by current normalizer |
| PaddleOCR | text → paragraph; formula → equation; figure → image; table_title → caption | Planned adapter vocabulary; real output verification pending |
| Chandra | section_header → heading; list_item → list; picture → image | Planned adapter vocabulary; real output verification pending |
| Vintern | section_header → heading; text → paragraph; formula → equation | Required structured adapter labels; model output is not assumed structured |

Unknown labels map to unknown with needs_review; adapter registration does not make an engine runnable.

### PDF.js scaling rule

For validated normalized coordinates on the same oriented page: left = x0 × rendered CSS width; top = y0 × rendered CSS height; width = (x1−x0) × rendered CSS width; height = (y1−y0) × rendered CSS height. Use canvas CSS size, not backing-store pixels: devicePixelRatio only controls raster sharpness.
When CropBox/rotation differs from the parser coordinate frame, the adapter must convert using verified source metadata before declaring normalized_0_1. Without evidence, keep geometry null; do not guess a rotation or clamp invalid boxes. Existing viewer alignment has only been verified on ordinary sample PDFs.

Migration `202611260002` adds nullable Page.rotation and Block evidence fields. No rewriting of existing documents is performed.

Status: implemented Page/Block/Span contract for MinerU 4; other engine adapters and mapping verification are deferred.
Fixture: `be/tests/fixtures/mineru_contract.json` is synthetic Vietnamese content following observed MinerU 4 output, not a copied user document.

## Coordinates and numbering

- External API `page_number` is 1-based. MinerU `page_idx` is 0-based; convert once in the normalizer.
- Bbox is `[left, top, right, bottom]`, top-left origin, finite floats, `0 <= left < right <= 1`, `0 <= top < bottom <= 1`.
- `coordinate_system = normalized_0_1` only accompanies validated geometry. Missing, inverted, non-finite or pixel-space geometry becomes null; retain original data in raw JSON.
- Dimensions are PDF points when known; unknown dimensions remain null. Viewer dimensions come from PDF.js, not guessed A4 sizes.
- Rotation/CropBox alignment has not been benchmarked. No implicit rotation or pixel-coordinate conversion is permitted; engine-specific transforms must be validated before support is claimed.

## Page

`id`, `document_id`, `page_number`, nullable `width`, `height`, `image_url`, `raw_text`.
One current page per document/page number. Dimensions are currently unknown in MinerU 4 normalization.

## Block

`id`, `document_id`, `page_id`, `page_number`, `block_type`, `text`, `corrected_text`, `bbox`, `reading_order`, `confidence`, `source_engine`, `raw_json`.
Expose canonical block types; preserve original labels in raw_json. Legacy stored rows can retain old labels until re-normalized.
Heading level is retained in `raw_json.level` and exposed in preview as `heading_level`.
Confidence is nullable; do not invent scores. Corrections are separate and cleared when source text changes.

## Span

`id`, `document_id`, `block_id`, `parse_run_id`, `page_number`, `reading_order`, `span_type`, `text`, `bbox`, `coordinate_system`, `confidence`.
Span order is 0-based within a block. Preserve exact inline text whitespace and source types (text, inline_equation, etc.).
Nested inline groups flatten in source order. Non-text content may have null text.
Missing span bbox stays null; never inherit a block bbox. OCR geometry and PDF.js text-layer geometry are distinct sources.
`raw_json` retains original inline content/styles for future adapters and rendering.

## Identity and provenance

- Persisted Page/Block IDs remain stable at unchanged page/reading-order positions during normalization. Position stability is not semantic identity across arbitrary document edits.
- Span IDs are deterministic from persisted block ID and inline order. Removed spans are deleted; repeating normalization does not duplicate them.
- `parse_run_id` identifies an `ocr_outputs.id` snapshot, not a background job ID. Null is allowed for legacy/test normalization without an OCR output.
- Current normalized tables are a mutable snapshot; historical raw OCR outputs are retained. They are not an immutable source graph.
- Preview block IDs are scoped to the OCR output and differ from persisted Block IDs. Preview nested spans use inline order, not persisted span IDs. Consumers must not pass preview IDs to persisted block filters.
- Engine version is not currently recorded reliably. Keep it unknown until adapters explicitly supply it; never infer a version from installed packages at read time.

## API and migration

- Existing `/documents/{id}/pages`, `/blocks`, `/preview` remain compatible.
- `/documents/{id}/spans` returns persisted spans, optionally filtered by `page_number` and/or persisted `block_id`.
- Preview includes nested span content for legacy raw outputs without changing database records on GET.
- Apply Alembic revision `202611260001` before starting updated backend processing. Existing documents have zero persisted spans until re-normalized; preview can still derive inline content from raw output.
- No automatic reprocessing of existing files or model calls on GET.

## Remaining work

Span text selection/overlay UI, source-version capture, immutable normalized parse snapshots, legacy backfill command, measured page rotation/transforms, and verification of multi-engine adapter mappings.
