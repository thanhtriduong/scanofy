"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AlertCircle, ArrowLeft, FileText, LoaderCircle } from "lucide-react";

import { DocumentContextPanel } from "@/components/reader/document-context-panel";
import { PdfDocumentViewer } from "@/components/reader/pdf-document-viewer";
import { AppSidebar } from "@/components/shell/app-sidebar";
import { StatusBadge } from "@/components/ui/status-badge";
import { getDocumentFileUrl, getDocumentPreview, getDocumentStatus, retryDocument } from "@/lib/api";
import type {
  DocumentPreviewBlock,
  DocumentPreviewResponse,
} from "@/types/documents";

type DocumentReaderProps = {
  documentId: string;
};

export function DocumentReader({ documentId }: DocumentReaderProps) {
  const [preview, setPreview] = useState<DocumentPreviewResponse | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);
  const [showGeometry, setShowGeometry] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingError, setProcessingError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    if (!preview || ["parsed", "completed", "failed", "awaiting_ocr"].includes(preview.document.status)) return;
    let cancelled = false;
    const timer = window.setInterval(async () => {
      try {
        const status = await getDocumentStatus(documentId);
        if (cancelled) return;
        setProcessingError(status.latest_job?.error_message ?? null);
        if (["parsed", "completed"].includes(status.status)) {
          const result = await getDocumentPreview(documentId);
          if (!cancelled) setPreview(result);
        } else {
          setPreview((current) => current ? { ...current, document: { ...current.document, status: status.status } } : current);
        }
      } catch { /* Keep the original readable during temporary status failures. */ }
    }, 2000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [documentId, preview]);

  async function retry() {
    setRetrying(true);
    try {
      await retryDocument(documentId);
      setPreview((current) => current ? { ...current, document: { ...current.document, status: "uploaded" } } : current);
      setProcessingError(null);
    } catch (reason) { setProcessingError(reason instanceof Error ? reason.message : "Không thể thử lại."); }
    finally { setRetrying(false); }
  }

  useEffect(() => {
    let cancelled = false;
    getDocumentPreview(documentId)
      .then((result) => {
        if (cancelled) return;
        setPreview(result);
        setPageNumber(result.pages[0]?.page_number ?? 1);
      })
      .catch((reason) => {
        if (!cancelled) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Không thể tải bản xem trước.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [documentId]);

  const selectedBlock =
    preview?.blocks.find((block) => block.id === selectedBlockId) ?? null;

  const changePage = useCallback((nextPage: number) => {
    setPageNumber(nextPage);
    if (selectedBlock?.page_number !== nextPage) {
      setSelectedBlockId(null);
    }
  }, [selectedBlock]);

  const navigateToBlock = useCallback((block: DocumentPreviewBlock) => {
    setPageNumber(block.page_number);
    setSelectedBlockId(block.id);
  }, []);

  if (error) {
    return <ReaderError message={error} />;
  }

  if (!preview) {
    return <ReaderLoading />;
  }

  const fileUrl = getDocumentFileUrl(documentId);
  const isPdf = preview.document.file_type === "pdf";

  return (
    <div className="min-h-screen bg-background lg:grid lg:grid-cols-[248px_minmax(0,1fr)]">
      <AppSidebar />
      <div className="min-w-0">
        <header className="sticky top-0 z-30 flex min-h-16 flex-wrap items-center gap-3 border-b border-border bg-background/95 px-4 py-3 backdrop-blur sm:px-6">
          <Link
            href="/"
            aria-label="Quay lại thư viện"
            className="grid h-9 w-9 shrink-0 place-items-center scanofy-control border border-border text-muted-foreground transition-colors hover:bg-surface hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          </Link>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold" title={preview.document.filename}>
              {preview.document.filename}
            </p>
            <p className="text-xs text-muted-foreground">Thư viện / Trình đọc</p>
          </div>
          <ModeSwitcher />
          <StatusBadge status={preview.document.status} />
        </header>

        <main className="grid min-h-[calc(100vh-4rem)] xl:grid-cols-[minmax(0,1fr)_380px]">
          <section className="min-w-0 bg-surface p-3 sm:p-5" aria-label="Tài liệu gốc">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-medium">
                <FileText className="h-4 w-4 text-primary" aria-hidden="true" />
                Tài liệu gốc
              </div>
              <a
                href={fileUrl}
                target="_blank"
                rel="noreferrer"
                className="text-sm font-medium text-primary hover:underline"
              >
                Mở file gốc
              </a>
            </div>

            {isPdf ? (
              <PdfDocumentViewer
                fileUrl={fileUrl}
                filename={preview.document.filename}
                pageNumber={pageNumber}
                blocks={["parsed", "completed"].includes(preview.document.status) ? preview.blocks : []}
                selectedBlockId={selectedBlockId}
                showGeometry={showGeometry}
                onPageChange={changePage}
                onSelectBlock={setSelectedBlockId}
                onToggleGeometry={() => setShowGeometry((current) => !current)}
              />
            ) : preview.document.file_type === "docx" ? (
              <div className="rounded-lg border bg-background p-8 text-sm leading-6"><p>File gốc đã sẵn sàng. Định dạng DOCX chưa hỗ trợ đọc trực tiếp trong trình duyệt.</p><a href={fileUrl} className="mt-4 inline-block text-primary underline">Tải file gốc để đọc</a></div>
            ) : (
              <div className="overflow-auto rounded-lg border border-border bg-muted p-4 sm:p-8">
                {/* The source is a document-scoped endpoint on the same application. */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={fileUrl}
                  alt={`Bản gốc ${preview.document.filename}`}
                  className="mx-auto max-h-[calc(100vh-10rem)] bg-background object-contain shadow-sm"
                />
              </div>
            )}
          </section>

          {["parsed", "completed"].includes(preview.document.status) ? <DocumentContextPanel
            blocks={preview.blocks}
            selectedBlock={selectedBlock}
            sourceEngine={preview.source_engine}
            onNavigate={navigateToBlock}
            onClearSelection={() => setSelectedBlockId(null)}
          /> : <aside className="border-l border-border p-6" aria-live="polite">
            <h2 className="text-lg font-medium">{preview.document.status === "failed" ? "Phân tích chưa thành công" : preview.document.status === "awaiting_ocr" ? "Đang chờ nhận dạng nội dung" : "Đang chuẩn bị cấu trúc tài liệu"}</h2>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">File gốc đã được lưu. Bạn có thể đọc ngay; mục lục và vùng nội dung sẽ xuất hiện khi phân tích hoàn tất.</p>
            {preview.document.status === "failed" ? <button type="button" onClick={() => void retry()} disabled={retrying} className="scanofy-control mt-5 h-10 bg-primary px-5 text-sm text-primary-foreground disabled:opacity-50">{retrying ? "Đang gửi yêu cầu…" : "Thử phân tích lại"}</button> : preview.document.status !== "awaiting_ocr" && <div aria-hidden="true" className="mt-6 space-y-4"><div className="h-4 w-4/5 animate-pulse rounded bg-muted" /><div className="h-4 w-3/5 animate-pulse rounded bg-muted" /><div className="h-4 w-4/5 animate-pulse rounded bg-muted" /></div>}
            {processingError && <details className="mt-5 text-xs text-muted-foreground"><summary>Thông tin xử lý nâng cao</summary><p className="mt-2 break-words">{processingError}</p></details>}
          </aside>}
        </main>
      </div>
    </div>
  );
}

function ModeSwitcher() {
  return (
    <div
      className="order-last flex w-full items-center rounded-full bg-muted p-1 sm:order-none sm:w-auto"
      aria-label="Chế độ tài liệu"
    >
      <span className="flex h-8 flex-1 items-center justify-center rounded-full bg-background px-4 text-sm font-medium sm:flex-none">
        Đọc
      </span>
      <span className="flex h-8 flex-1 cursor-not-allowed items-center justify-center px-4 text-sm text-muted-foreground sm:flex-none">
        Tri thức
      </span>
      <span className="flex h-8 flex-1 cursor-not-allowed items-center justify-center px-4 text-sm text-muted-foreground sm:flex-none">
        Luyện tập
      </span>
    </div>
  );
}

function ReaderLoading() {
  return (
    <div className="grid min-h-screen place-items-center bg-surface">
      <div className="text-center">
        <LoaderCircle className="mx-auto h-6 w-6 animate-spin text-primary" aria-hidden="true" />
        <p className="mt-3 text-sm font-medium">Đang chuẩn bị trình đọc</p>
      </div>
    </div>
  );
}

function ReaderError({ message }: { message: string }) {
  return (
    <div className="grid min-h-screen place-items-center bg-surface p-6">
      <div className="max-w-md rounded-lg border border-danger/20 bg-background p-6 text-center">
        <AlertCircle className="mx-auto h-6 w-6 text-danger" aria-hidden="true" />
        <h1 className="mt-3 text-lg font-semibold">Không thể mở tài liệu</h1>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{message}</p>
        <Link
          href="/"
          className="mt-5 inline-flex h-9 items-center scanofy-control bg-primary px-4 text-sm font-semibold text-primary-foreground"
        >
          Về thư viện
        </Link>
      </div>
    </div>
  );
}
