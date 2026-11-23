"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  FileText,
  Layers3,
  LoaderCircle,
} from "lucide-react";

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
    pageBlocks.find((block) => block.id === selectedBlockId) ?? null;
  const pageIndex = preview?.pages.findIndex(
    (page) => page.page_number === pageNumber,
  ) ?? -1;

  if (error) {
    return <ReaderError message={error} />;
  }

  if (!preview) {
    return <ReaderLoading />;
  }

  const isPdf = preview.document.file_type === "pdf";
  const fileUrl = getDocumentFileUrl(documentId);

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
            <p className="text-xs text-muted-foreground">
              Thư viện / Bản xem trước
            </p>
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
                Mở trong tab mới
              </a>
            </div>
            <div className="overflow-hidden rounded-lg border border-border bg-background">
              {isPdf ? (
                <iframe
                  src={fileUrl}
                  title={`Bản gốc ${preview.document.filename}`}
                  className="h-[calc(100vh-8.5rem)] min-h-[620px] w-full"
                />
              ) : (
                // The file endpoint is document-scoped; no external image host is involved.
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={fileUrl}
                  alt={`Bản gốc ${preview.document.filename}`}
                  className="mx-auto max-h-[calc(100vh-8.5rem)] object-contain"
                />
              )}
            </div>
          </section>

          <aside className="border-t border-border bg-background xl:border-l xl:border-t-0">
            <div className="border-b border-border p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 text-sm font-semibold">
                    <Layers3 className="h-4 w-4 text-primary" aria-hidden="true" />
                    Cấu trúc MinerU
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {preview.blocks.length} block · {preview.pages.length} trang
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowGeometry((current) => !current)}
                  aria-pressed={showGeometry}
                  className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm font-medium transition-colors hover:bg-surface"
                >
                  {showGeometry ? (
                    <Eye className="h-4 w-4" aria-hidden="true" />
                  ) : (
                    <EyeOff className="h-4 w-4" aria-hidden="true" />
                  )}
                  Layout
                </button>
              </div>
            </div>

            {preview.pages.length === 0 ? (
              <div className="p-8 text-center">
                <Layers3 className="mx-auto h-6 w-6 text-muted-foreground" aria-hidden="true" />
                <p className="mt-3 text-sm font-medium">Chưa có cấu trúc trang</p>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">
                  Tài liệu chưa có output MinerU để hiển thị layout.
                </p>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between border-b border-border px-4 py-3">
                  <button
                    type="button"
                    disabled={pageIndex <= 0}
                    onClick={() => {
                      setPageNumber(preview.pages[pageIndex - 1].page_number);
                      setSelectedBlockId(null);
                    }}
                    aria-label="Trang trước"
                    className="grid h-8 w-8 place-items-center rounded-md border border-border disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                  </button>
                  <p className="text-sm font-medium">
                    Trang {pageNumber} / {preview.pages.length}
                  </p>
                  <button
                    type="button"
                    disabled={pageIndex >= preview.pages.length - 1}
                    onClick={() => {
                      setPageNumber(preview.pages[pageIndex + 1].page_number);
                      setSelectedBlockId(null);
                    }}
                    aria-label="Trang sau"
                    className="grid h-8 w-8 place-items-center rounded-md border border-border disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <ChevronRight className="h-4 w-4" aria-hidden="true" />
                  </button>
                </div>

                <div className="max-h-[calc(100vh-12rem)] overflow-y-auto p-4">
                  <LayoutMap
                    blocks={pageBlocks}
                    selectedBlockId={selectedBlockId}
                    showGeometry={showGeometry}
                    onSelect={setSelectedBlockId}
                  />
                  <BlockInspector block={selectedBlock} blocks={pageBlocks} onSelect={setSelectedBlockId} />
                </div>
              </>
            )}
          </aside>
        </main>
      </div>
    </div>
  );
}

function ModeSwitcher() {
  return (
    <div className="order-last flex w-full items-center rounded-md bg-muted p-1 sm:order-none sm:w-auto" aria-label="Chế độ tài liệu">
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

function LayoutMap({
  blocks,
  selectedBlockId,
  showGeometry,
  onSelect,
}: {
  blocks: DocumentPreviewBlock[];
  selectedBlockId: string | null;
  showGeometry: boolean;
  onSelect: (id: string) => void;
}) {
  const geometricBlocks = blocks.filter(
    (block) =>
      block.coordinate_system === "normalized_0_1" && block.bbox?.length === 4,
  );

  return (
    <div>
      <p className="mb-2 text-xs font-medium text-muted-foreground">Bản đồ layout</p>
      <div className="relative mx-auto aspect-[1/1.414] w-full max-w-[320px] overflow-hidden rounded-md border border-border-strong bg-surface-raised shadow-sm">
        {showGeometry &&
          geometricBlocks.map((block) => {
            const [left, top, right, bottom] = block.bbox as number[];
            const selected = block.id === selectedBlockId;
            return (
              <button
                key={block.id}
                type="button"
                onClick={() => onSelect(block.id)}
                title={block.text ?? block.block_type}
                aria-label={`Chọn block ${block.block_type}`}
                className={`absolute overflow-hidden border text-left text-xs transition-colors focus:z-20 ${
                  selected
                    ? "z-10 border-primary bg-primary/15"
                    : "border-primary/35 bg-info-soft/70 hover:border-primary hover:bg-primary/10"
                }`}
                style={{
                  left: `${left * 100}%`,
                  top: `${top * 100}%`,
                  width: `${Math.max((right - left) * 100, 1)}%`,
                  height: `${Math.max((bottom - top) * 100, 0.6)}%`,
                }}
              >
                <span className="sr-only">{block.text}</span>
              </button>
            );
          })}
        {geometricBlocks.length === 0 && (
          <div className="grid h-full place-items-center px-8 text-center text-xs leading-5 text-muted-foreground">
            Trang này không có geometry hợp lệ; nội dung vẫn xuất hiện trong danh sách block.
          </div>
        )}
      </div>
    </div>
  );
}

function BlockInspector({
  block,
  blocks,
  onSelect,
}: {
  block: DocumentPreviewBlock | null;
  blocks: DocumentPreviewBlock[];
  onSelect: (id: string) => void;
}) {
  if (block) {
    return (
      <div className="mt-4 rounded-lg border border-primary/25 bg-info-soft p-4">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-medium text-primary">{formatBlockType(block.block_type)}</p>
          <p className="text-xs text-muted-foreground">Block {block.reading_order ?? "—"}</p>
        </div>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-foreground">
          {block.text || "Block này không có nội dung chữ."}
        </p>
      </div>
    );
  }

  return (
    <div className="mt-4">
      <p className="mb-2 text-xs font-medium text-muted-foreground">Block trên trang</p>
      <div className="space-y-2">
        {blocks.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onSelect(item.id)}
            className="w-full rounded-md border border-border px-3 py-2 text-left transition-colors hover:border-border-strong hover:bg-surface"
          >
            <span className="block text-xs font-medium text-primary">
              {formatBlockType(item.block_type)}
            </span>
            <span className="mt-1 block line-clamp-2 text-sm leading-5 text-foreground">
              {item.text || "Không có nội dung chữ"}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

function formatBlockType(type: string): string {
  const labels: Record<string, string> = {
    doc_title: "Tiêu đề tài liệu",
    paragraph_title: "Tiêu đề mục",
    text: "Đoạn văn",
    image: "Hình ảnh",
    table: "Bảng",
    equation: "Công thức",
  };
  return labels[type] ?? type.replaceAll("_", " ");
}

function ReaderLoading() {
  return (
    <div className="grid min-h-screen place-items-center bg-surface">
      <div className="text-center">
        <LoaderCircle className="mx-auto h-6 w-6 animate-spin text-primary" aria-hidden="true" />
        <p className="mt-3 text-sm font-medium">Đang chuẩn bị bản xem trước</p>
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
        <Link href="/" className="mt-5 inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground">
          Về thư viện
        </Link>
      </div>
    </div>
  );
}
