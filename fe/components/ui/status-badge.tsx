import { documentStatusLabel } from "@/lib/document-ui";

const statusStyles: Record<string, string> = {
  failed: "border-danger/20 bg-danger-soft text-danger",
  parsed: "border-success/20 bg-success-soft text-success",
  completed: "border-success/20 bg-success-soft text-success",
  awaiting_ocr: "border-warning/20 bg-warning-soft text-warning",
  processing: "border-info/20 bg-info-soft text-info",
  normalizing: "border-info/20 bg-info-soft text-info",
  uploaded: "border-info/20 bg-info-soft text-info",
  queued: "border-border bg-surface text-muted-foreground",
  idle: "border-border bg-surface text-muted-foreground",
};

const dotStyles: Record<string, string> = {
  failed: "bg-danger",
  parsed: "bg-success",
  completed: "bg-success",
  awaiting_ocr: "bg-warning",
  processing: "bg-info",
  normalizing: "bg-info",
  uploaded: "bg-info",
  queued: "bg-muted-foreground",
  idle: "bg-muted-foreground",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex h-7 shrink-0 items-center gap-2 rounded-md border px-2.5 text-xs font-medium ${
        statusStyles[status] ?? statusStyles.idle
      }`}
    >
      <span
        aria-hidden="true"
        className={`h-1.5 w-1.5 rounded-full ${dotStyles[status] ?? dotStyles.idle}`}
      />
      {documentStatusLabel(status)}
    </span>
  );
}
