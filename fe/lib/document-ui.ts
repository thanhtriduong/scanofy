const terminalStatuses = new Set([
  "awaiting_ocr",
  "parsed",
  "completed",
  "failed",
]);

export function isTerminalDocumentStatus(status: string) {
  return terminalStatuses.has(status);
}

export function formatBytes(bytes?: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export function formatDocumentDate(value: string) {
  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function documentStatusLabel(status: string) {
  const labels: Record<string, string> = {
    idle: "Chưa chọn",
    queued: "Đang chờ",
    uploaded: "Đã tải lên",
    processing: "Đang phân tích",
    normalizing: "Đang chuẩn hóa",
    awaiting_ocr: "Chờ OCR",
    parsed: "Sẵn sàng",
    completed: "Hoàn tất",
    failed: "Thất bại",
  };
  return labels[status] ?? status.replaceAll("_", " ");
}
