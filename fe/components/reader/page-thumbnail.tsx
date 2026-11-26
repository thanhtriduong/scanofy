"use client";

import { useEffect, useRef, useState } from "react";
import type { PDFDocumentProxy, RenderTask } from "pdfjs-dist";

export function PageThumbnail({ pdf, pageNumber, active, onSelect }: {
  pdf: PDFDocumentProxy;
  pageNumber: number;
  active: boolean;
  onSelect: () => void;
}) {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [near, setNear] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    const button = buttonRef.current;
    if (!button) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        setNear(true);
        observer.disconnect();
      }
    }, { root: button.closest("nav"), rootMargin: "200px" });
    observer.observe(button);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!near) return;
    let disposed = false;
    let task: RenderTask | undefined;
    async function render() {
      try {
        const page = await pdf.getPage(pageNumber);
        if (disposed || !canvasRef.current) return;
        const base = page.getViewport({ scale: 1 });
        const viewport = page.getViewport({ scale: 120 / base.width });
        const canvas = canvasRef.current;
        canvas.width = Math.ceil(viewport.width * 2);
        canvas.height = Math.ceil(viewport.height * 2);
        const context = canvas.getContext("2d");
        if (!context) return;
        task = page.render({ canvas, canvasContext: context, viewport, transform: [2, 0, 0, 2, 0, 0] });
        await task.promise;
      } catch (reason) {
        if (!disposed && !(reason instanceof Error && reason.name === "RenderingCancelledException")) setError(true);
      }
    }
    void render();
    return () => { disposed = true; task?.cancel(); };
  }, [near, pageNumber, pdf]);

  return (
    <button ref={buttonRef} type="button" onClick={onSelect} aria-label={`Đến trang ${pageNumber}`} aria-current={active ? "page" : undefined} className={`block w-full rounded-lg border-2 p-2 text-center transition-colors ${active ? "border-primary bg-info-soft text-primary" : "border-transparent text-muted-foreground hover:border-border-strong hover:bg-muted"}`}>
      <div className="flex min-h-36 items-center justify-center overflow-hidden rounded-sm bg-background">
        {error ? <span className="p-2 text-xs">Không tải được ảnh xem trước</span> : <canvas ref={canvasRef} className="h-auto w-full" aria-hidden="true" />}
      </div>
      <span className="mt-2 block text-xs font-medium tabular-nums">Trang {pageNumber}</span>
    </button>
  );
}
