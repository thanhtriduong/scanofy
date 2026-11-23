"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AlertCircle, ArrowLeft, FileText, LoaderCircle } from "lucide-react";

import { DocumentContextPanel } from "@/components/reader/document-context-panel";
import { PdfDocumentViewer } from "@/components/reader/pdf-document-viewer";
import { AppSidebar } from "@/components/shell/app-sidebar";
import { StatusBadge } from "@/components/ui/status-badge";
import { getDocumentFileUrl, getDocumentPreview } from "@/lib/api";
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

  const pageBlocks = useMemo(
    () =>
      preview?.blocks.filter((block) => block.page_number === pageNumber) ?? [],
    [pageNumber, preview],
  );
  const selectedBlock =
    preview?.blocks.find((block) => block.id === selectedBlockId) ?? null;

  function changePage(nextPage: number) {
    setPageNumber(nextPage);
    if (selectedBlock?.page_number !== nextPage) {
      setSelectedBlockId(null);
    }
  }

  function navigateToBlock(block: DocumentPreviewBlock) {
    setPageNumber(block.page_number);
    setSelectedBlockId(block.id);
  }

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
            className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-border text-muted-foreground transition-colors hover:bg-surface hover:text-foreground"
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
                blocks={pageBlocks}
                selectedBlockId={selectedBlockId}
                showGeometry={showGeometry}
                onPageChange={changePage}
                onSelectBlock={setSelectedBlockId}
                onToggleGeometry={() => setShowGeometry((current) => !current)}
              />
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

          <DocumentContextPanel
            blocks={preview.blocks}
            selectedBlock={selectedBlock}
            sourceEngine={preview.source_engine}
            onNavigate={navigateToBlock}
            onClearSelection={() => setSelectedBlockId(null)}
          />
        </main>
      </div>
    </div>
  );
}

function ModeSwitcher() {
  return (
    <div
      className="order-last flex w-full items-center rounded-md bg-muted p-1 sm:order-none sm:w-auto"
      aria-label="Chế độ tài liệu"
    >
      <span className="flex h-8 flex-1 items-center justify-center rounded bg-background px-4 text-sm font-medium shadow-sm sm:flex-none">
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
          className="mt-5 inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground"
        >
          Về thư viện
        </Link>
      </div>
    </div>
  );
}
