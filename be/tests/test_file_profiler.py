from zipfile import ZipFile

import pytest
from PIL import Image

from app.services.file_profiler import FileProfiler
from app.services.router import DocumentRouter
from tests.pdf_fixtures import write_pdf


@pytest.mark.parametrize("kinds,classification,ratio,scan,engine", [
    (("text", "rotated"), "digital_pdf", 1, 0, "mineru"),
    (("scan", "scan"), "scanned_pdf", 0, 1, "paddleocr"),
    (("text", "scan"), "mixed", 0.5, 0.5, "mineru"),
    (("blank",), "sparse_or_blank", 0, 0, "mineru"),
])
def test_pdf_measurements_and_route(tmp_path, kinds, classification, ratio, scan, engine):
    path = tmp_path / "fixture.pdf"
    write_pdf(path, kinds)
    profile = FileProfiler().profile(path, "pdf")
    assert profile["page_count"] == len(kinds)
    assert profile["classification"] == classification
    assert profile["text_layer_ratio"] == ratio
    assert profile["scan_score"] == scan
    assert profile["pages"][0]["width"] == 600
    assert profile["pages"][0]["height"] == 800
    assert profile["handwriting_score"] is None
    assert DocumentRouter().choose_engine(profile)["engine"] == engine
    if "rotated" in kinds:
        assert profile["pages"][1]["rotation"] == 90


def test_encrypted_and_broken_pdf_are_not_invented_profiles(tmp_path):
    path = tmp_path / "locked.pdf"
    write_pdf(path, encrypted=True)
    with pytest.raises(ValueError, match="mật khẩu"):
        FileProfiler().profile(path, "pdf")
    path.write_bytes(b"not a pdf")
    with pytest.raises(ValueError):
        FileProfiler().profile(path, "pdf")


def test_image_metadata_does_not_claim_handwriting(tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (80, 120)).save(path)
    profile = FileProfiler().profile(path, "png")
    assert (profile["image_width"], profile["image_height"]) == (80, 120)
    assert profile["handwriting_score"] is None
    assert profile["scan_score"] is None


def test_docx_does_not_invent_paginated_page_count(tmp_path):
    path = tmp_path / "document.docx"
    with ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", '<document><text>Bài học tiếng Việt</text></document>')
    profile = FileProfiler().profile(path, "docx")
    assert profile["text_char_count"] > 0
    assert profile["page_count"] is None
    assert profile["text_layer_ratio"] is None
    assert DocumentRouter().choose_engine(profile)["engine"] == "mineru"
