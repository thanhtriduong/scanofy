"""Render matching Vietnamese SVG/PNG report figures using installed Pillow."""
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/diagrams"
W, H = 1680, 1710
image = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(image)
font_path = "C:/Windows/Fonts/arial.ttf"
fonts = {size: ImageFont.truetype(font_path, size) for size in (18, 21, 23, 29, 40)}
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>']


def text(x, y, value, size=23, color="#201f20", center=False):
    draw.text((x, y), value, font=fonts[size], fill=color, anchor="mt" if center else "lt")
    svg.append(f'<text x="{x}" y="{y + size * .86}" font-family="Arial, sans-serif" font-size="{size}" fill="{color}" text-anchor="{"middle" if center else "start"}">{escape(value)}</text>')


def box(x, y, width, title, detail, fill="#f7f6f6", stroke="#c8c7c7"):
    height = 100
    draw.rounded_rectangle((x, y, x + width, y + height), radius=12, fill=fill, outline=stroke, width=2)
    svg.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    text(x + width / 2, y + 19, title, 23, center=True)
    text(x + width / 2, y + 57, detail, 18, "#494949", True)


def arrow(x1, y1, x2, y2, color="#606060"):
    draw.line((x1, y1, x2, y2), fill=color, width=3)
    if x1 == x2:
        sign = 1 if y2 > y1 else -1
        points = [(x2, y2), (x2 - 7, y2 - 12 * sign), (x2 + 7, y2 - 12 * sign)]
    else:
        sign = 1 if x2 > x1 else -1
        points = [(x2, y2), (x2 - 12 * sign, y2 - 7), (x2 - 12 * sign, y2 + 7)]
    draw.polygon(points, fill=color)
    svg.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="3"/><polygon points="{" ".join(f"{x},{y}" for x,y in points)}" fill="{color}"/>')


text(80, 55, "SCANOFY · LUỒNG XỬ LÝ TÀI LIỆU MINERU", 40)
text(80, 115, "Xử lý nền song song với đọc PDF · Sơ đồ theo mã nguồn triển khai", 23, "#494949")
text(520, 175, "BACKEND VÀ DỮ LIỆU", 29, center=True)
text(1350, 175, "TRẢI NGHIỆM NGƯỜI DÙNG", 29, center=True)
steps = [
    (230, "1. Upload và lưu file gốc", "Kiểm tra đầu vào · Tạo Document và job queued"),
    (385, "2. File Profiler", "Đo trang, text, ảnh, kích thước và rotation"),
    (540, "3. Router", "Chọn MinerU cho PDF số / hỗn hợp và DOCX"),
    (695, "4. MinerU CLI", "mineru-kit parse · Output riêng từng lần chạy"),
    (850, "5. Kiểm tra artifact và lưu nguồn", "middle_json.json + markdown.md · Manifest, hash và raw output"),
    (1005, "6. Chuẩn hóa Page / Block / Span", "Kiểm tra schema, bbox, reading order và số trang"),
    (1160, "7. Lưu dữ liệu chuẩn hóa", "Giao dịch database · Giữ ID theo vị trí khi normalize lặp"),
    (1315, "8. Hoàn tất", "Document: parsed · Job: completed"),
]
for index, (y, title, detail) in enumerate(steps):
    box(80, y, 880, title, detail, "#eef2ff" if index == 7 else "#f7f6f6", "#2e5bff" if index == 7 else "#c8c7c7")
    if index:
        arrow(520, steps[index - 1][0] + 100, 520, y)
box(1100, 230, 500, "Mở Document Workspace", "Ngay sau upload response; không đợi MinerU")
arrow(960, 280, 1100, 280, "#2e5bff")
box(1100, 385, 500, "Đọc PDF gốc", "Cuộn trang · Zoom · Thumbnail", "#eef2ff", "#2e5bff")
arrow(1350, 330, 1350, 385)
box(1100, 540, 500, "Nhánh OCR khác", "awaiting_ocr · Adapter chưa tích hợp")
arrow(960, 590, 1100, 590)
box(1100, 850, 500, "Theo dõi trạng thái", "Polling; đang xử lý → parsed / failed")
arrow(1600, 435, 1640, 435)
arrow(1640, 435, 1640, 900)
arrow(1640, 900, 1600, 900)
box(1100, 1005, 500, "Nếu phân tích lỗi", "Vẫn đọc file gốc · Thử lại tạo job mới", "#fff7ed", "#a16207")
arrow(1350, 950, 1350, 1005)
box(1100, 1315, 500, "Mở cấu trúc tài liệu", "Mục lục · Overlay block · Nội dung nguồn", "#eef2ff", "#2e5bff")
arrow(960, 1365, 1100, 1365, "#2e5bff")
text(80, 1480, "Nhánh lỗi áp dụng cho profiler, CLI, artifact, normalize và lưu database.", 21)
text(80, 1525, "Retry chạy lại từ File Profiler. Renormalize dùng raw đã lưu, mặc định dry-run và không gọi model.", 21)
text(80, 1570, "PaddleOCR / Chandra / Vintern là nhánh dự kiến; sơ đồ không khẳng định đã có adapter hoạt động.", 21)
text(80, 1630, "Nguồn: backend Scanofy · Hình mô tả kiến trúc, không phải số liệu benchmark OCR.", 18, "#606060")
svg.append("</svg>")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "mineru-pipeline.svg").write_text("\n".join(svg), encoding="utf-8")
image.save(OUT / "mineru-pipeline.png")
print(OUT / "mineru-pipeline.png")
