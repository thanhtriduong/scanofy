"""PaddleOCR 3.x line output -> Scanofy Page/Block/Span, in rendered coordinates."""
import math


def validate_paddle_output(raw: dict) -> None:
    if not isinstance(raw, dict) or raw.get("schema") != "scanofy.paddleocr.v1":
        raise ValueError("Unsupported PaddleOCR raw schema.")
    pages = raw.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("PaddleOCR output must contain pages.")
    for number, page in enumerate(pages, 1):
        if not isinstance(page, dict) or type(page.get("page_number")) is not int or page["page_number"] != number:
            raise ValueError("PaddleOCR page numbers must be contiguous.")
        for key in ("width", "height"):
            value = page.get(key)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError("PaddleOCR raster dimensions must be positive.")
        result = page.get("result", {})
        if not isinstance(result, dict):
            raise ValueError("PaddleOCR page requires a result object.")
        texts, polygons, scores = (result.get(key) for key in ("rec_texts", "rec_polys", "rec_scores"))
        if not isinstance(texts, list) or not all(isinstance(text, str) for text in texts):
            raise ValueError("PaddleOCR result requires rec_texts[].")
        if not isinstance(polygons, list) or len(polygons) != len(texts):
            raise ValueError("PaddleOCR text/polygon count mismatch.")
        if not isinstance(scores, list) or len(scores) != len(texts):
            raise ValueError("PaddleOCR text/score count mismatch.")
        if any(type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1 for score in scores):
            raise ValueError("Invalid PaddleOCR recognition confidence.")


def polygon_bbox(polygon, width, height):
    if not isinstance(polygon, list) or len(polygon) < 4:
        return None
    if any(not isinstance(point, list) or len(point) != 2 or
           any(type(v) not in (float, int) or not math.isfinite(v) for v in point) for point in polygon):
        return None
    xs, ys = [p[0] for p in polygon], [p[1] for p in polygon]
    box = [min(xs) / width, min(ys) / height, max(xs) / width, max(ys) / height]
    if not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
        return None
    return box


def normalize_paddle_output(envelope: dict) -> dict:
    raw = envelope["raw_output"]
    validate_paddle_output(raw)
    pages, blocks = [], []
    for page in raw["pages"]:
        number, result = page["page_number"], page["result"]
        pages.append({"page_number": number, "width": page["width"], "height": page["height"],
                      "raw_text": "\n".join(result["rec_texts"])})
        for index, (text, polygon, score) in enumerate(zip(result["rec_texts"], result["rec_polys"], result["rec_scores"])):
            bbox = polygon_bbox(polygon, page["width"], page["height"])
            geometry = {"bbox": bbox, "coordinate_system": "normalized_0_1" if bbox else None}
            blocks.append({"page_number": number, "block_type": "paragraph", "text": text,
                           "reading_order": index, "confidence": score, "source_engine": "paddleocr",
                           "needs_review": bbox is None, **geometry,
                           "raw_json": {"polygon": polygon, "granularity": "line", "coordinate_frame": "rendered_page"},
                           "spans": [{"reading_order": 0, "span_type": "text", "text": text,
                                      "confidence": score, **geometry}]})
    return {"source": "paddleocr", "status": "completed", "pages": pages, "blocks": blocks}
