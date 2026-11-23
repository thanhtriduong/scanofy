import { AlertCircle, Database, Route, Workflow } from "lucide-react";

import { StatusBadge } from "@/components/ui/status-badge";
import type {
  DocumentRecord,
  DocumentStatusResponse,
} from "@/types/documents";

type ProcessingPanelProps = {
  document: DocumentRecord | null;
  status: DocumentStatusResponse | null;
};

export function ProcessingPanel({ document, status }: ProcessingPanelProps) {
  const currentStatus = status?.status ?? document?.status ?? "idle";
  const latestJob = status?.latest_job;

  return (
    <section className="rounded-lg border border-border bg-surface-raised p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold leading-7">Trạng thái xử lý</h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Theo dõi hồ sơ, bộ định tuyến và bước xử lý hiện tại.
          </p>
        </div>
        <div aria-live="polite">
          <StatusBadge status={currentStatus} />
        </div>
      </div>

      {!document ? (
        <div className="mt-5 rounded-lg border border-dashed border-border-strong bg-surface px-5 py-9 text-center">
          <p className="text-sm font-medium">Chưa có tài liệu được chọn</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            Chọn một tài liệu gần đây hoặc tải file mới để xem tiến trình.
          </p>
        </div>
      ) : (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <InfoItem icon={Database} label="Tài liệu" value={document.filename} />
            <InfoItem
              icon={Route}
              label="Bộ xử lý"
              value={status?.router_decision?.engine ?? "Đang xác định"}
            />
            <InfoItem
              icon={Workflow}
              label="Bước hiện tại"
              value={latestJob?.current_step?.replaceAll("_", " ") ?? "Chưa bắt đầu"}
            />
          </div>

          {latestJob?.error_message && (
            <div
              role="alert"
              className="mt-4 flex items-start gap-3 rounded-lg border border-danger/20 bg-danger-soft p-4 text-sm text-danger"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <div>
                <p className="font-medium">Không thể xử lý tài liệu</p>
                <p className="mt-1 break-words leading-6">{latestJob.error_message}</p>
              </div>
            </div>
          )}

          <details className="mt-4 rounded-lg border border-border bg-surface">
            <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-foreground">
              Chi tiết kỹ thuật
            </summary>
            <div className="grid gap-3 border-t border-border p-3 md:grid-cols-2">
              <DiagnosticBlock label="File profile" value={status?.profile} />
              <DiagnosticBlock label="Router decision" value={status?.router_decision} />
            </div>
          </details>
        </>
      )}
    </section>
  );
}

function InfoItem({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Database;
  label: string;
  value: string;
}) {
  return (
    <div className="min-w-0 rounded-lg border border-border bg-background p-4">
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <Icon className="h-4 w-4 text-primary" aria-hidden="true" />
        {label}
      </div>
      <p className="mt-2 truncate text-sm font-medium text-foreground" title={value}>
        {value}
      </p>
    </div>
  );
}

function DiagnosticBlock({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="min-w-0">
      <p className="mb-2 text-xs font-medium text-muted-foreground">{label}</p>
      <pre className="max-h-56 overflow-auto rounded-md bg-foreground p-3 text-xs leading-5 text-background">
        {JSON.stringify(value ?? {}, null, 2)}
      </pre>
    </div>
  );
}
