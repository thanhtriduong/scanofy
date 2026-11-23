"use client";

import { useEffect, useRef, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  LoaderCircle,
  Maximize2,
  Minus,
  Plus,
} from "lucide-react";
import type { PDFDocumentProxy, RenderTask } from "pdfjs-dist";

import type { DocumentPreviewBlock } from "@/types/documents";

type PdfDocumentViewerProps = {
  fileUrl: string;
  filename: string;
  pageNumber: number;
  blocks: DocumentPreviewBlock[];
  selectedBlockId: string | null;
  showGeometry: boolean;
  onPageChange: (pageNumber: number) => void;
  onSelectBlock: (blockId: string) => void;
  onToggleGeometry: () => void;
};

export function PdfDocumentViewer({
  fileUrl,
  filename,
  pageNumber,
  blocks,
  selectedBlockId,
  showGeometry,
  onPageChange,
  onSelectBlock,
  onToggleGeometry,
}: PdfDocumentViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const viewerRef = useRef<HTMLDivElement>(null);
  const renderTaskRef = useRef<RenderTask | null>(null);
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null);
  const [zoom, setZoom] = useState(1);
  const [fitToWidth, setFitToWidth] = useState(true);
  const [isRendering, setIsRendering] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let disposed = false;
    let document: PDFDocumentProxy | null = null;
    let worker: Worker | null = null;

    async function loadPdf() {
      try {
        const pdfjs = await import("pdfjs-dist");
        worker = new Worker(
          new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url),
          { type: "module" },
        );
        pdfjs.GlobalWorkerOptions.workerPort = worker;
        const absoluteUrl = new URL(fileUrl, window.location.origin).href;
        const task = pdfjs.getDocument({ url: absoluteUrl });
        document = await task.promise;
        if (!disposed) {
          setPdf(document);
          setError(null);
        }
      } catch (reason) {
        if (!disposed) {
          setError(
            reason instanceof Error ? reason.message : "Không thể đọc file PDF.",
          );
        }
      }
    }

    void loadPdf();
    return () => {
      disposed = true;
      renderTaskRef.current?.cancel();
      void document?.cleanup();
      worker?.terminate();
    };
  }, [fileUrl]);

  useEffect(() => {
    if (!pdf || !canvasRef.current) return;
    const currentPdf = pdf;
    let disposed = false;

    async function renderPage() {
      setIsRendering(true);
      renderTaskRef.current?.cancel();
      try {
        const page = await currentPdf.getPage(pageNumber);
        if (disposed || !canvasRef.current) return;
        if (fitToWidth && viewerRef.current) {
          const baseViewport = page.getViewport({ scale: 1 });
          const horizontalPadding = window.innerWidth < 640 ? 32 : 64;
          const fittedZoom = Math.min(
            1.5,
            Math.max(0.5, (viewerRef.current.clientWidth - horizontalPadding) / baseViewport.width),
          );
          if (Math.abs(fittedZoom - zoom) > 0.01) {
            setZoom(fittedZoom);
            return;
          }
        }
        const viewport = page.getViewport({ scale: zoom });
        const outputScale = window.devicePixelRatio || 1;
        const canvas = canvasRef.current;
        const context = canvas.getContext("2d");
        if (!context) throw new Error("Trình duyệt không hỗ trợ PDF canvas.");

        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);
        canvas.style.width = `${Math.floor(viewport.width)}px`;
        canvas.style.height = `${Math.floor(viewport.height)}px`;
        const transform =
          outputScale === 1
            ? undefined
            : [outputScale, 0, 0, outputScale, 0, 0];

        const renderTask = page.render({
          canvas,
          canvasContext: context,
          viewport,
          transform,
        });
        renderTaskRef.current = renderTask;
        await renderTask.promise;
        if (!disposed) {
          setIsRendering(false);
          setError(null);
        }
      } catch (reason) {
        if (disposed || (reason instanceof Error && reason.name === "RenderingCancelledException")) {
          return;
        }
        setError(
          reason instanceof Error ? reason.message : "Không thể render trang PDF.",
        );
        setIsRendering(false);
      }
    }

    void renderPage();
    return () => {
      disposed = true;
      renderTaskRef.current?.cancel();
    };
  }, [fitToWidth, pageNumber, pdf, zoom]);

  const pageCount = pdf?.numPages ?? 0;
  const geometricBlocks = blocks.filter(
    (block) =>
      block.coordinate_system === "normalized_0_1" && block.bbox?.length === 4,
  );

  return (
    <div className="flex min-h-[calc(100vh-8rem)] flex-col overflow-hidden rounded-lg border border-border bg-background">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-3 py-2">
        <div className="flex items-center gap-2">
          <ToolbarButton
            label="Trang trước"
            disabled={!pdf || pageNumber <= 1}
            onClick={() => onPageChange(pageNumber - 1)}
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          </ToolbarButton>
          <p className="min-w-24 text-center text-sm font-medium">
            Trang {pageNumber} / {pageCount || "—"}
          </p>
          <ToolbarButton
            label="Trang sau"
            disabled={!pdf || pageNumber >= pageCount}
            onClick={() => onPageChange(pageNumber + 1)}
          >
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          </ToolbarButton>
        </div>

        <div className="flex items-center gap-2">
          <ToolbarButton
            label="Thu nhỏ"
            disabled={zoom <= 0.5}
            onClick={() => {
              setFitToWidth(false);
              setZoom((value) => Math.max(0.5, value - 0.15));
            }}
          >
            <Minus className="h-4 w-4" aria-hidden="true" />
          </ToolbarButton>
          <span className="min-w-12 text-center text-xs text-muted-foreground">
            {Math.round(zoom * 100)}%
          </span>
          <ToolbarButton
            label="Phóng to"
            disabled={zoom >= 2}
            onClick={() => {
              setFitToWidth(false);
              setZoom((value) => Math.min(2, value + 0.15));
            }}
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
          </ToolbarButton>
          <ToolbarButton
            label="Vừa chiều rộng"
            disabled={fitToWidth}
            onClick={() => setFitToWidth(true)}
          >
            <Maximize2 className="h-4 w-4" aria-hidden="true" />
          </ToolbarButton>
          <button
            type="button"
            onClick={onToggleGeometry}
            aria-pressed={showGeometry}
            className={`ml-1 inline-flex h-9 items-center gap-2 rounded-md border px-3 text-sm font-medium transition-colors ${
              showGeometry
                ? "border-primary/35 bg-info-soft text-primary"
                : "border-border text-muted-foreground hover:bg-surface hover:text-foreground"
            }`}
          >
            {showGeometry ? (
              <Eye className="h-4 w-4" aria-hidden="true" />
            ) : (
              <EyeOff className="h-4 w-4" aria-hidden="true" />
            )}
            Vùng block
          </button>
        </div>
      </div>

      <div ref={viewerRef} className="relative flex flex-1 justify-center overflow-auto bg-muted p-4 sm:p-8">
        {error ? (
          <div className="m-auto max-w-md rounded-lg border border-danger/20 bg-background p-5 text-center">
            <p className="text-sm font-medium text-danger">Không thể hiển thị PDF</p>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">{error}</p>
            <a
              href={fileUrl}
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground"
            >
              Mở file gốc
            </a>
          </div>
        ) : (
          <div className="relative h-fit w-fit bg-background shadow-sm" aria-label={`Trang ${pageNumber} của ${filename}`}>
            <canvas ref={canvasRef} className="block max-w-none" />
            {geometricBlocks.map((block) => (
              <BlockRegion
                key={block.id}
                block={block}
                selected={block.id === selectedBlockId}
                showGeometry={showGeometry}
                onSelect={() => onSelectBlock(block.id)}
              />
            ))}
            {isRendering && (
              <div className="absolute inset-0 grid min-h-96 min-w-72 place-items-center bg-background/85">
                <div className="text-center">
                  <LoaderCircle className="mx-auto h-5 w-5 animate-spin text-primary" aria-hidden="true" />
                  <p className="mt-2 text-xs text-muted-foreground">Đang render trang</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function BlockRegion({
  block,
  selected,
  showGeometry,
  onSelect,
}: {
  block: DocumentPreviewBlock;
  selected: boolean;
  showGeometry: boolean;
  onSelect: () => void;
}) {
  const [left, top, right, bottom] = block.bbox as number[];
  return (
    <button
      type="button"
      onClick={onSelect}
      title={block.text ?? block.block_type}
      aria-label={`Chọn ${formatBlockType(block.block_type)} trên trang ${block.page_number}`}
      className={`absolute transition-colors focus:z-20 ${
        selected
          ? "z-10 border-2 border-primary bg-primary/15"
          : showGeometry
            ? "border border-primary/30 bg-info-soft/20 hover:border-primary hover:bg-primary/10"
            : "border border-transparent bg-transparent hover:border-primary/60 hover:bg-primary/10"
      }`}
      style={{
        left: `${left * 100}%`,
        top: `${top * 100}%`,
        width: `${Math.max((right - left) * 100, 0.8)}%`,
        height: `${Math.max((bottom - top) * 100, 0.5)}%`,
      }}
    >
      <span className="sr-only">{block.text}</span>
    </button>
  );
}

function ToolbarButton({
  label,
  disabled,
  onClick,
  children,
}: {
  label: string;
  disabled: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
      className="grid h-9 w-9 place-items-center rounded-md border border-border text-muted-foreground transition-colors hover:bg-surface hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
    >
      {children}
    </button>
  );
}

function formatBlockType(type: string): string {
  const labels: Record<string, string> = {
    doc_title: "tiêu đề tài liệu",
    paragraph_title: "tiêu đề mục",
    text: "đoạn văn",
    image: "hình ảnh",
    table: "bảng",
    equation: "công thức",
  };
  return labels[type] ?? type.replaceAll("_", " ");
}
