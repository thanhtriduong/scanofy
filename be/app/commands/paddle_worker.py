"""Isolated CPU inference, one process per document; no database access."""
import argparse
from contextlib import closing
from importlib.metadata import version
import json
import math
from pathlib import Path

from PIL import Image, ImageOps


def raster_pages(source: Path, output: Path, dpi: int, max_pages: int, max_pixels: int):
    if source.suffix.lower() != ".pdf":
        with Image.open(source) as original:
            if original.width * original.height > max_pixels:
                raise ValueError("Input image exceeds PADDLEOCR_MAX_PIXELS.")
            image = ImageOps.exif_transpose(original).convert("RGBA")
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            path = output / "page-0001.png"
            background.save(path)
            yield 1, path, background.size, {"kind": "image", "exif_transposed": True}
        return
    import pypdfium2 as pdfium
    with pdfium.PdfDocument(source) as pdf:
        if not 0 < len(pdf) <= max_pages:
            raise ValueError("PDF exceeds PADDLEOCR_MAX_PAGES or has no pages.")
        for index in range(len(pdf)):
            with closing(pdf[index]) as page:
                width, height = page.get_size()
                scale = dpi / 72
                if math.ceil(width * scale) * math.ceil(height * scale) > max_pixels:
                    raise ValueError("Rendered PDF page exceeds PADDLEOCR_MAX_PIXELS.")
                bitmap = page.render(scale=scale)
                try:
                    image = bitmap.to_pil().convert("RGB")
                    path = output / f"page-{index + 1:04d}.png"
                    image.save(path)
                    yield index + 1, path, image.size, {"kind": "pdf_render", "dpi": dpi,
                          "rendered_width_pt": width, "rendered_height_pt": height,
                          "coordinate_frame": "cropbox_with_native_rotation"}
                finally:
                    bitmap.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lang", default="vi")
    parser.add_argument("--dpi", type=int, default=144)
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--max-pixels", type=int, default=25_000_000)
    args = parser.parse_args()
    if not 72 <= args.dpi <= 300 or args.max_pages < 1 or args.max_pixels < 1:
        raise ValueError("Invalid PaddleOCR rendering limits.")
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError("Install optional OCR dependencies: python -m pip install -r requirements-paddleocr.txt") from exc
    # PP-OCRv3 Latin recognition supports vi. Geometry-changing preprocessing is off.
    ocr = PaddleOCR(lang=args.lang, ocr_version="PP-OCRv3", device="cpu",
                    use_doc_orientation_classify=False, use_doc_unwarping=False,
                    use_textline_orientation=False, enable_mkldnn=False, cpu_threads=4)
    pages = []
    for number, path, (width, height), transform in raster_pages(args.input, args.output, args.dpi, args.max_pages, args.max_pixels):
        results = list(ocr.predict(str(path)))
        if len(results) != 1:
            raise ValueError("Expected one PaddleOCR result per rendered page.")
        result = results[0].json["res"]
        # Preserve engine JSON without numpy arrays or in-memory image objects.
        (args.output / f"page-{number:04d}.json").write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        pages.append({"page_number": number, "width": width, "height": height,
                      "raster_artifact": path.name, "transform": transform, "result": result})
    raw = {"schema": "scanofy.paddleocr.v1", "metadata": {
        "paddleocr_version": version("paddleocr"), "paddlepaddle_version": version("paddlepaddle"),
        "lang": args.lang, "ocr_version": "PP-OCRv3", "device": "cpu",
        "preprocessing": {"doc_orientation": False, "unwarping": False, "textline_orientation": False}}, "pages": pages}
    from app.services.paddleocr_normalizer import validate_paddle_output
    validate_paddle_output(raw)
    (args.output / "paddleocr.json").write_text(json.dumps(raw, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    (args.output / "markdown.md").write_text("\n\n---\n\n".join("\n".join(page["result"]["rec_texts"]) for page in pages), encoding="utf-8")


if __name__ == "__main__":
    main()
