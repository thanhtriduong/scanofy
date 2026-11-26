"""Mapping contract for adapters; it does not enable unsupported engines."""
CANONICAL_TYPES = {
    "title", "heading", "paragraph", "list", "table", "image", "equation",
    "caption", "header", "footer", "page_number", "footnote", "reference", "unknown",
}
ALIASES = {
    "mineru": {"doc_title": "title", "paragraph_title": "heading", "text": "paragraph", "ref_text": "reference", "page_footnote": "footnote", "image_caption": "caption", "table_caption": "caption", "interline_equation": "equation"},
    "paddleocr": {"doc_title": "title", "paragraph_title": "heading", "text": "paragraph", "figure": "image", "formula": "equation", "figure_title": "caption", "table_title": "caption", "reference_content": "reference"},
    "chandra": {"text": "paragraph", "section_header": "heading", "picture": "image", "formula": "equation", "list_item": "list"},
    "vintern": {"text": "paragraph", "section_header": "heading", "figure": "image", "formula": "equation"},
}


def canonical_block_type(engine: str, source_type: str) -> str:
    candidate = ALIASES.get(engine, {}).get(source_type, source_type)
    return candidate if candidate in CANONICAL_TYPES else "unknown"
