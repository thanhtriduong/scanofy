"""Measure input structure without OCR or handwriting inference."""
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree

from PIL import Image
from pypdf import PdfReader

MIN_TEXT_CHARACTERS = 20
MAX_TEXT_STREAM_BYTES = 10 * 1024 * 1024


class FileProfiler:
    def profile(self, file_path: Path, file_type: str) -> dict:
        file_type = file_type.lower().lstrip(".")
        result = {
            "profile_version": "1.0", "file_type": file_type,
            "size_bytes": file_path.stat().st_size, "page_count": None,
            "text_layer_ratio": None, "scan_score": None,
            "handwriting_score": None, "classification": "unknown",
            "pages": [], "warnings": [],
            "thresholds": {"min_text_characters": MIN_TEXT_CHARACTERS},
        }
        if file_type == "pdf":
            return self._pdf(file_path, result)
        if file_type == "docx":
            try:
                with ZipFile(file_path) as archive:
                    info = archive.getinfo("word/document.xml")
                    if info.file_size > MAX_TEXT_STREAM_BYTES:
                        raise ValueError("DOCX document XML exceeds profiling limit.")
                    root = ElementTree.fromstring(archive.read(info))
                    text = "".join(root.itertext())
                    result["text_char_count"] = sum(c.isalnum() for c in text)
                    result["classification"] = "digital_document"
                return result
            except (BadZipFile, KeyError, ElementTree.ParseError) as exc:
                raise ValueError("Không thể đọc cấu trúc DOCX. File có thể bị hỏng.") from exc
        if file_type in {"jpg", "jpeg", "png", "webp"}:
            try:
                with Image.open(file_path) as image:
                    width, height = image.size
                    image.verify()
                result.update(classification="image", image_width=width, image_height=height)
                return result
            except (OSError, ValueError) as exc:
                raise ValueError("Không thể đọc file ảnh.") from exc
        raise ValueError(f"Unsupported profiling type: {file_type}")

    def _pdf(self, file_path: Path, result: dict) -> dict:
        try:
            with file_path.open("rb") as source:
                reader = PdfReader(source, strict=False)
                if reader.is_encrypted and not reader.decrypt(""):
                    raise ValueError("PDF được bảo vệ bằng mật khẩu; hãy tải bản đã mở khóa.")
                result["page_count"] = len(reader.pages)
                if not reader.pages:
                    raise ValueError("PDF không có trang.")
                for index, page in enumerate(reader.pages):
                    measured = {
                        "page_number": index + 1,
                        "width": float(page.cropbox.width) * float(page.user_unit),
                        "height": float(page.cropbox.height) * float(page.user_unit),
                        "rotation": int(page.rotation) % 360,
                        "text_char_count": None, "image_count": None,
                        "has_useful_text": None, "classification": "unknown",
                    }
                    try:
                        content = page.get_contents()
                        if content is not None and len(content.get_data()) > MAX_TEXT_STREAM_BYTES:
                            result["warnings"].append(f"page_{index + 1}:text_stream_limit")
                        else:
                            text = page.extract_text() or ""
                            measured["text_char_count"] = sum(c.isalnum() for c in text)
                            measured["has_useful_text"] = measured["text_char_count"] >= MIN_TEXT_CHARACTERS
                        measured["image_count"] = len(page.images.keys())
                        if measured["has_useful_text"]:
                            measured["classification"] = "text"
                        elif measured["has_useful_text"] is False:
                            measured["classification"] = "scan_candidate" if measured["image_count"] else "sparse_or_blank"
                    except Exception:
                        result["warnings"].append(f"page_{index + 1}:extraction_unavailable")
                    result["pages"].append(measured)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Không thể đọc PDF. File có thể bị hỏng hoặc không đúng định dạng.") from exc

        pages = result["pages"]
        # Unknown pages do not become falsely positive scan/text evidence.
        if all(page["has_useful_text"] is not None and page["image_count"] is not None for page in pages):
            text_pages = sum(page["has_useful_text"] for page in pages)
            scan_pages = sum(page["classification"] == "scan_candidate" for page in pages)
            result["text_layer_ratio"] = text_pages / len(pages)
            result["scan_score"] = scan_pages / len(pages)
            result["classification"] = (
                "mixed" if text_pages and scan_pages else "digital_pdf" if text_pages else
                "scanned_pdf" if scan_pages else "sparse_or_blank"
            )
        return result
