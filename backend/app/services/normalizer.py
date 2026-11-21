class Normalizer:
    """Placeholder normalizer for future multi-engine OCR output."""

    def normalize(self, raw_output: dict) -> dict:
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
