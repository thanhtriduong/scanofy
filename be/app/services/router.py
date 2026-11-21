from dataclasses import asdict, dataclass


@dataclass(slots=True)
class RouterDecision:
    engine: str
    reason: str
    fallback_engine: str | None = None


class DocumentRouter:
    """Week 1 routing stub based on the project draft logic."""

    def choose_engine(self, profile: dict) -> dict:
        file_type = profile.get("file_type")
        text_layer_ratio = profile.get("text_layer_ratio") or 0
        scan_score = profile.get("scan_score") or 0
        handwriting_score = profile.get("handwriting_score") or 0

        if file_type in {"pdf", "docx"} and text_layer_ratio >= 0.6:
            return asdict(RouterDecision(engine="mineru", reason="digital_document_or_text_layer"))

        if file_type in {"jpg", "jpeg", "png", "webp"}:
            return asdict(RouterDecision(engine="chandra", reason="image_input"))

        if scan_score >= 0.5 or handwriting_score >= 0.4:
            return asdict(RouterDecision(engine="chandra", reason="scan_or_handwriting_signal"))

        return asdict(
            RouterDecision(
                engine="mineru_with_fallback",
                reason="default_placeholder_route",
                fallback_engine="vintern",
            )
        )
