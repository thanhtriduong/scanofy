import { FileText, Inbox } from "lucide-react";

import { StatusBadge } from "@/components/ui/status-badge";
import { formatDocumentDate } from "@/lib/document-ui";
import type { DocumentRecord } from "@/types/documents";

type DocumentListProps = {
  documents: DocumentRecord[];
  activeDocumentId?: string;
  isLoading: boolean;
  onSelect: (document: DocumentRecord) => void;
};

export function DocumentList({
  documents,
  activeDocumentId,
  isLoading,
  onSelect,
}: DocumentListProps) {
  return (
    <aside className="rounded-lg border border-border bg-surface-raised">
      <div className="border-b border-border px-4 py-4">
        <h2 className="text-sm font-semibold">Tài liệu gần đây</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          {documents.length} tài liệu trong thư viện
        </p>
      </div>

      <div className="max-h-[calc(100vh-13rem)] space-y-1 overflow-y-auto p-2">
        {isLoading && documents.length === 0 ? (
          Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="h-20 animate-pulse rounded-md bg-muted"
              aria-hidden="true"
            />
          ))
        ) : documents.length === 0 ? (
          <div className="px-4 py-12 text-center">
            <Inbox className="mx-auto h-6 w-6 text-muted-foreground" aria-hidden="true" />
            <p className="mt-3 text-sm font-medium">Thư viện đang trống</p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              Tải lên tài liệu đầu tiên để bắt đầu.
            </p>
          </div>
        ) : (
          documents.map((document) => {
            const isActive = activeDocumentId === document.id;
            return (
              <button
                key={document.id}
                type="button"
                onClick={() => onSelect(document)}
                aria-pressed={isActive}
                className={`w-full rounded-md border px-3 py-3 text-left transition-colors ${
                  isActive
                    ? "border-primary/30 bg-info-soft"
                    : "border-transparent hover:border-border hover:bg-surface"
                }`}
              >
                <span className="flex items-start gap-3">
                  <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-md border border-border bg-background text-muted-foreground">
                    <FileText className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span
                      className="block truncate text-sm font-medium text-foreground"
                      title={document.filename}
                    >
                      {document.filename}
                    </span>
                    <span className="mt-2 flex flex-wrap items-center gap-2">
                      <StatusBadge status={document.status} />
                      <span className="text-xs text-muted-foreground">
                        {formatDocumentDate(document.created_at)}
                      </span>
                    </span>
                  </span>
                </span>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}
