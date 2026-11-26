# Scanofy document contract v1

Status: implemented Page/Block/Span contract for MinerU 4; other engine mappings are deferred.
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
Preserve engine block types, including unknown types; no lossy cross-engine mapping yet.
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

Span text selection/overlay UI, source-version capture, immutable normalized parse snapshots, legacy backfill command, page rotation metadata/transforms, and validated multi-engine mappings.
