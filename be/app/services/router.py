from dataclasses import asdict, dataclass


@dataclass(slots=True)
class RouterDecision:
    engine: str
    reason: str
    fallback_engine: str | None = None


class DocumentRouter:
    """Route from measured evidence; planned engines stay explicit."""

    def choose_engine(self, profile: dict) -> dict:
        file_type = profile.get("file_type")
        text_layer_ratio = profile.get("text_layer_ratio") or 0
        scan_score = profile.get("scan_score") or 0
        handwriting_score = profile.get("handwriting_score") or 0

        if handwriting_score >= 0.4:
            return asdict(RouterDecision(engine="chandra", reason="explicit_handwriting_signal"))

        if file_type == "docx":
            return asdict(RouterDecision(engine="mineru", reason="docx_document"))

        if file_type == "pdf" and profile.get("classification") == "mixed":
            return asdict(RouterDecision(engine="mineru", reason="mixed_pdf_requires_page_aware_parsing"))

        if file_type == "pdf" and text_layer_ratio >= 0.6:
            return asdict(RouterDecision(engine="mineru", reason="digital_document_or_text_layer"))

        if file_type in {"jpg", "jpeg", "png", "webp"}:
            return asdict(RouterDecision(engine="paddleocr", reason="image_requires_ocr_handwriting_unknown"))

        if scan_score >= 0.5:
            return asdict(RouterDecision(engine="paddleocr", reason="image_pages_without_useful_text"))

        return asdict(
            RouterDecision(
                engine="mineru",
                reason="pdf_sparse_or_unknown_requires_parser",
            )
        )
