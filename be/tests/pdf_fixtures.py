from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject, NumberObject


def write_pdf(path, kinds=("text",), encrypted=False):
    writer = PdfWriter()
    for kind in kinds:
        page = writer.add_blank_page(width=600, height=800)
        stream = DecodedStreamObject()
        if kind == "scan":
            image = DecodedStreamObject()
            image.set_data(b"\xff\xff\xff")
            image.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Image"), NameObject("/Width"): NumberObject(1), NameObject("/Height"): NumberObject(1), NameObject("/ColorSpace"): NameObject("/DeviceRGB"), NameObject("/BitsPerComponent"): NumberObject(8)})
            page[NameObject("/Resources")] = DictionaryObject({NameObject("/XObject"): DictionaryObject({NameObject("/Im0"): writer._add_object(image)})})
            stream.set_data(b"q 600 0 0 800 0 0 cm /Im0 Do Q")
        elif kind in {"text", "rotated"}:
            font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
            page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
            stream.set_data(b"BT /F1 12 Tf 30 700 Td (This is a digital educational document with selectable text.) Tj ET")
            if kind == "rotated":
                page.rotate(90)
        else:
            stream.set_data(b"")
        page[NameObject("/Contents")] = writer._add_object(stream)
    if encrypted:
        writer.encrypt("secret")
    with path.open("wb") as output:
        writer.write(output)
