"use client";

import { useEffect, useRef, useState } from "react";
import {
  PanelLeft,
  X,
  Eye,
  EyeOff,
  LoaderCircle,
  Maximize2,
  Minus,
  Plus,
} from "lucide-react";
import type { PDFDocumentProxy, RenderTask } from "pdfjs-dist";

import type { DocumentPreviewBlock } from "@/types/documents";
import { PageThumbnail } from "@/components/reader/page-thumbnail";

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
  const viewerRef = useRef<HTMLDivElement>(null);
  const pageElementsRef = useRef(new Map<number, HTMLDivElement>());
  const visibilityRef = useRef(new Map<number, number>());
  const visiblePageRef = useRef(1);
  const navigationTargetRef = useRef<number | null>(null);
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null);
  const [zoom, setZoom] = useState(1);
  const [fitToWidth, setFitToWidth] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showThumbnails, setShowThumbnails] = useState(false);
  const thumbnailToggleRef = useRef<HTMLButtonElement>(null);

  function closeThumbnails() {
    setShowThumbnails(false);
    thumbnailToggleRef.current?.focus();
  }

  function jumpToPage(number: number) {
    const viewer = viewerRef.current;
    const target = pageElementsRef.current.get(number);
    if (!viewer || !target) return;
    navigationTargetRef.current = number;
    viewer.scrollTo({
      top: viewer.scrollTop + target.getBoundingClientRect().top - viewer.getBoundingClientRect().top - 16,
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
    });
    onPageChange(number);
    if (window.innerWidth < 640) closeThumbnails();
  }

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
      void document?.cleanup();
      worker?.terminate();
    };
  }, [fileUrl]);

  useEffect(() => {
    if (!pdf || !fitToWidth || !viewerRef.current) return;
    const currentPdf = pdf;
    const viewer = viewerRef.current;
    let disposed = false;

    async function fitPages() {
      const firstPage = await currentPdf.getPage(1);
      if (disposed) return;
      const baseViewport = firstPage.getViewport({ scale: 1 });
      const horizontalPadding = window.innerWidth < 640 ? 32 : 64;
      const fittedZoom = Math.min(
        1.5,
        Math.max(0.5, (viewer.clientWidth - horizontalPadding) / baseViewport.width),
      );
      setZoom((current) =>
        Math.abs(current - fittedZoom) > 0.01 ? fittedZoom : current,
      );
    }

    void fitPages();
    const resizeObserver = new ResizeObserver(() => void fitPages());
    resizeObserver.observe(viewer);
    return () => {
      disposed = true;
      resizeObserver.disconnect();
    };
  }, [fitToWidth, pdf]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!pdf || !viewer) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const candidate = Number(
            (entry.target as HTMLElement).dataset.pageNumber,
          );
          visibilityRef.current.set(candidate, entry.intersectionRatio);
        }

        let mostVisiblePage = visiblePageRef.current;
        let largestRatio = 0;
        for (const [candidate, ratio] of visibilityRef.current) {
          if (ratio > largestRatio) {
            mostVisiblePage = candidate;
            largestRatio = ratio;
          }
        }
        if (largestRatio <= 0 || mostVisiblePage === visiblePageRef.current) return;

        const target = navigationTargetRef.current;
        if (target !== null && mostVisiblePage !== target) return;
        navigationTargetRef.current = null;
        visiblePageRef.current = mostVisiblePage;
        onPageChange(mostVisiblePage);
      },
      {
        root: viewer,
        threshold: [0.1, 0.25, 0.5, 0.75, 0.9],
      },
    );

    for (const element of pageElementsRef.current.values()) {
      observer.observe(element);
    }
    return () => observer.disconnect();
  }, [onPageChange, pdf]);

  useEffect(() => {
    if (!pdf || selectedBlockId || pageNumber === visiblePageRef.current) return;
    const target = pageElementsRef.current.get(pageNumber);
    if (!target) return;
    navigationTargetRef.current = pageNumber;
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [pageNumber, pdf, selectedBlockId]);

  useEffect(() => {
    if (!selectedBlockId || !viewerRef.current) return;
    const viewer = viewerRef.current;
    const region = Array.from(viewer.querySelectorAll<HTMLElement>("[data-block-id]"))
      .find((element) => element.dataset.blockId === selectedBlockId);
    if (!region) return;
    const block = blocks.find((item) => item.id === selectedBlockId);
    if (!block) return;
    navigationTargetRef.current = block.page_number;
    const scrollToSource = () => {
      const target = region.getBoundingClientRect();
      const container = viewer.getBoundingClientRect();
      viewer.scrollTo({
        top: viewer.scrollTop + target.top - container.top - viewer.clientHeight / 3,
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
      });
    };
    const observer = new ResizeObserver(scrollToSource);
    observer.observe(region);
    return () => observer.disconnect();
  }, [blocks, pdf, selectedBlockId]);

  const pageCount = pdf?.numPages ?? 0;
  const pages = Array.from({ length: pageCount }, (_, index) => index + 1);

  return (
    <div className="flex h-[calc(100vh-10.5rem)] min-h-[560px] flex-col overflow-hidden rounded-lg border border-border bg-background">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-3 py-2">
        <div className="flex items-center gap-2">
          <button ref={thumbnailToggleRef} type="button" disabled={!pdf} aria-expanded={showThumbnails} aria-controls="pdf-thumbnails" onClick={() => setShowThumbnails((current) => !current)} className={`scanofy-control inline-flex h-9 items-center gap-2 border px-3 text-sm font-medium disabled:opacity-40 ${showThumbnails ? "border-primary/30 bg-info-soft text-primary" : "border-border hover:bg-surface"}`}>
            <PanelLeft className="h-4 w-4" aria-hidden="true" /> Các trang
          </button>
          <span className="text-xs tabular-nums text-muted-foreground" aria-live="polite">{pageNumber} / {pageCount || "—"}</span>
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
            className={`ml-1 inline-flex h-9 items-center gap-2 scanofy-control border px-3 text-sm font-medium transition-colors ${
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

      <div className="relative flex min-h-0 flex-1">
      {showThumbnails && pdf && (
        <aside id="pdf-thumbnails" aria-label="Ảnh thu nhỏ các trang" onKeyDown={(event) => { if (event.key === "Escape") closeThumbnails(); }} className="absolute inset-y-0 left-0 z-20 flex w-44 shrink-0 flex-col border-r border-border bg-surface sm:static sm:w-40">
          <div className="flex items-center justify-between px-3 py-2"><h2 className="text-sm font-medium">{pageCount} trang</h2><button type="button" onClick={closeThumbnails} aria-label="Đóng danh sách trang" className="scanofy-control grid h-8 w-8 place-items-center hover:bg-muted"><X className="h-4 w-4" aria-hidden="true" /></button></div>
          <nav className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3" aria-label="Chuyển trang PDF">
            {pages.map((number) => <PageThumbnail key={number} pdf={pdf} pageNumber={number} active={number === pageNumber} onSelect={() => jumpToPage(number)} />)}
          </nav>
        </aside>
      )}
      <div
        ref={viewerRef}
        data-pdf-scroll
        className="relative min-w-0 flex-1 overflow-auto bg-muted px-4 py-6 sm:px-8"
      >
        {error ? (
          <PdfError message={error} fileUrl={fileUrl} />
        ) : !pdf ? (
          <div className="grid h-full place-items-center">
            <div className="text-center">
              <LoaderCircle className="mx-auto h-5 w-5 animate-spin text-primary" aria-hidden="true" />
              <p className="mt-2 text-xs text-muted-foreground">Đang tải tài liệu</p>
            </div>
          </div>
        ) : (
          <div className="mx-auto flex w-fit min-w-full flex-col items-center gap-6">
            {pages.map((currentPage) => (
              <div
                key={currentPage}
                ref={(element) => {
                  if (element) pageElementsRef.current.set(currentPage, element);
                  else pageElementsRef.current.delete(currentPage);
                }}
                data-page-number={currentPage}
                className="scroll-mt-4"
              >
                <p className="mb-2 text-center text-xs font-medium text-muted-foreground">
                  Trang {currentPage}
                </p>
                <PdfPage
                  pdf={pdf}
                  filename={filename}
                  pageNumber={currentPage}
                  zoom={zoom}
                  blocks={blocks.filter((block) => block.page_number === currentPage)}
                  selectedBlockId={selectedBlockId}
                  showGeometry={showGeometry}
                  onSelectBlock={onSelectBlock}
                />
              </div>
            ))}
          </div>
        )}
      </div>
      </div>
    </div>
  );
}

function PdfPage({
  pdf,
  filename,
  pageNumber,
  zoom,
  blocks,
  selectedBlockId,
  showGeometry,
  onSelectBlock,
}: {
  pdf: PDFDocumentProxy;
  filename: string;
  pageNumber: number;
  zoom: number;
  blocks: DocumentPreviewBlock[];
  selectedBlockId: string | null;
  showGeometry: boolean;
  onSelectBlock: (blockId: string) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const renderTaskRef = useRef<RenderTask | null>(null);
  const [isRendering, setIsRendering] = useState(true);
  const [nearViewport, setNearViewport] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        setNearViewport(true);
        observer.disconnect();
      }
    }, { root: canvas.closest("[data-pdf-scroll]"), rootMargin: "900px" });
    observer.observe(canvas);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let disposed = false;

    async function renderPage() {
      setIsRendering(true);
      renderTaskRef.current?.cancel();
      try {
        const page = await pdf.getPage(pageNumber);
        if (disposed || !canvasRef.current) return;
        const viewport = page.getViewport({ scale: zoom });
        const outputScale = window.devicePixelRatio || 1;
        const canvas = canvasRef.current;
        canvas.style.width = `${Math.floor(viewport.width)}px`;
        canvas.style.height = `${Math.floor(viewport.height)}px`;
        if (!nearViewport) return;
        const context = canvas.getContext("2d");
        if (!context) return;

        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);
        canvas.style.width = `${Math.floor(viewport.width)}px`;
        canvas.style.height = `${Math.floor(viewport.height)}px`;
        const transform =
          outputScale === 1
            ? undefined
            : [outputScale, 0, 0, outputScale, 0, 0];
        const task = page.render({
          canvas,
          canvasContext: context,
          viewport,
          transform,
        });
        renderTaskRef.current = task;
        await task.promise;
        if (!disposed) setIsRendering(false);
      } catch (reason) {
        if (
          !disposed &&
          !(reason instanceof Error && reason.name === "RenderingCancelledException")
        ) {
          setIsRendering(false);
        }
      }
    }

    void renderPage();
    return () => {
      disposed = true;
      renderTaskRef.current?.cancel();
    };
  }, [nearViewport, pageNumber, pdf, zoom]);

  const geometricBlocks = blocks.filter(
    (block) =>
      block.coordinate_system === "normalized_0_1" && block.bbox?.length === 4,
  );

  return (
    <div
      className="relative h-fit w-fit bg-background shadow-sm"
      aria-label={`Trang ${pageNumber} của ${filename}`}
    >
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
          <LoaderCircle className="h-5 w-5 animate-spin text-primary" aria-hidden="true" />
        </div>
      )}
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
      data-block-id={block.id}
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

function PdfError({ message, fileUrl }: { message: string; fileUrl: string }) {
  return (
    <div className="m-auto max-w-md rounded-lg border border-danger/20 bg-background p-5 text-center">
      <p className="text-sm font-medium text-danger">Không thể hiển thị PDF</p>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">{message}</p>
      <a
        href={fileUrl}
        target="_blank"
        rel="noreferrer"
        className="mt-4 inline-flex h-9 items-center scanofy-control bg-primary px-4 text-sm font-semibold text-primary-foreground"
      >
        Mở file gốc
      </a>
    </div>
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
      className="grid h-9 w-9 place-items-center scanofy-control border border-border text-muted-foreground transition-colors hover:bg-surface hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
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
