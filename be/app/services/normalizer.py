import math


class Normalizer:
    """Normalize parser output into Scanofy's page and block contract."""

    def normalize(self, raw_output: dict) -> dict:
        parser_output = raw_output.get("raw_output") or raw_output
        mineru_pages = parser_output.get("pages") if isinstance(parser_output, dict) else None
        if isinstance(mineru_pages, list) and mineru_pages:
            return self._normalize_mineru_pages(raw_output, mineru_pages)

        markdown = raw_output.get("markdown_output") or ""
        if markdown:
            return {
                "pages": [
                    {
                        "page_number": 1,
                        "width": None,
                        "height": None,
                        "image_url": None,
                        "raw_text": markdown,
                    }
                ],
                "blocks": [
                    {
                        "page_number": 1,
                        "block_type": "paragraph",
                        "text": markdown,
                        "corrected_text": None,
                        "bbox": None,
                        "reading_order": 1,
                        "confidence": raw_output.get("average_confidence"),
                        "source_engine": raw_output.get("engine", "unknown"),
                        "raw_json": {
                            "markdown_path": raw_output.get("markdown_path"),
                            "json_path": raw_output.get("json_path"),
                        },
                    }
                ],
                "source": raw_output.get("engine", "unknown"),
                "status": "completed",
            }

        return {
            "pages": [],
            "blocks": [],
            "source": raw_output.get("engine", "unknown"),
            "status": "not_implemented",
        }

    def _normalize_mineru_pages(self, envelope: dict, mineru_pages: list[dict]) -> dict:
        pages: list[dict] = []
        blocks: list[dict] = []
        source_engine = envelope.get("engine", "mineru")

        for page_position, raw_page in enumerate(mineru_pages):
            page_number = int(raw_page.get("page_idx", page_position)) + 1
            page_text: list[str] = []
            for reading_order, raw_block in enumerate(raw_page.get("blocks") or [], 1):
                text = self._extract_text(raw_block.get("content"))
                if text:
                    page_text.append(text)
                bbox = self._valid_bbox(raw_block.get("bbox"))
                blocks.append(
                    {
                        "page_number": page_number,
                        "block_type": raw_block.get("type", "unknown"),
                        "text": text or None,
                        "corrected_text": None,
                        "bbox": bbox,
                        "reading_order": raw_block.get("index", reading_order),
                        "confidence": raw_block.get("confidence"),
                        "source_engine": source_engine,
                        "spans": self._normalize_spans(raw_block.get("content")),
                        "raw_json": {
                            **raw_block,
                            "coordinate_system": "normalized_0_1" if bbox else None,
                        },
                    }
                )

            pages.append(
                {
                    "page_number": page_number,
                    "width": None,
                    "height": None,
                    "image_url": None,
                    "raw_text": "\n\n".join(page_text) or None,
                }
            )

        return {
            "pages": pages,
            "blocks": blocks,
            "source": source_engine,
            "status": "completed",
        }

    def _extract_text(self, value: object) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "".join(self._extract_text(item) for item in value).strip()
        if isinstance(value, dict):
            return self._extract_text(value.get("content"))
        return ""

    def _normalize_spans(self, content: object) -> list[dict]:
        if isinstance(content, str):
            content = [{"type": "text", "content": content}]
        if not isinstance(content, list):
            return []
        spans = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("content"), list):
                spans.extend(self._normalize_spans(item["content"]))
                continue
            bbox = self._valid_bbox(item.get("bbox"))
            spans.append({
                "reading_order": len(spans),
                "span_type": item.get("type", "unknown"),
                "text": self._extract_text(item.get("content")) or None,
                "bbox": bbox,
                "coordinate_system": "normalized_0_1" if bbox else None,
                "confidence": item.get("confidence"),
                "raw_json": item,
            })
        for index, span in enumerate(spans):
            span["reading_order"] = index
        return spans

    def _valid_bbox(self, value: object) -> list[float] | None:
        if not isinstance(value, list) or len(value) != 4:
            return None
        if not all(type(coordinate) in (int, float) and math.isfinite(coordinate) for coordinate in value):
            return None
        left, top, right, bottom = value
        if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
            return None
        return [float(coordinate) for coordinate in value]
