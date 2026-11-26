"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Check,
  Clipboard,
  FileSearch,
  Languages,
  ListTree,
  MessageCircleQuestion,
  Sparkles,
  X,
} from "lucide-react";

import type { DocumentPreviewBlock } from "@/types/documents";

type DocumentContextPanelProps = {
  blocks: DocumentPreviewBlock[];
  selectedBlock: DocumentPreviewBlock | null;
  sourceEngine: string | null;
  onNavigate: (block: DocumentPreviewBlock) => void;
  onClearSelection: () => void;
};

export function DocumentContextPanel({
  blocks,
  selectedBlock,
  sourceEngine,
  onNavigate,
  onClearSelection,
}: DocumentContextPanelProps) {
  const outline = useMemo(
    () =>
      blocks.filter((block) =>
        ["doc_title", "paragraph_title", "title", "heading"].includes(block.block_type),
      ),
    [blocks],
  );

  return (
    <aside className="border-t border-border bg-background xl:border-l xl:border-t-0">
      {selectedBlock ? (
        <SelectedBlockPanel
          block={selectedBlock}
          sourceEngine={sourceEngine}
          onClose={onClearSelection}
        />
      ) : (
        <OutlinePanel outline={outline} blocks={blocks} onNavigate={onNavigate} />
      )}
    </aside>
  );
}

function OutlinePanel({
  outline,
  blocks,
  onNavigate,
}: {
  outline: DocumentPreviewBlock[];
  blocks: DocumentPreviewBlock[];
  onNavigate: (block: DocumentPreviewBlock) => void;
}) {
  const pagesWithContent = new Set(blocks.map((block) => block.page_number)).size;
  const geometryCount = blocks.filter(
    (block) => block.coordinate_system === "normalized_0_1" && block.bbox,
  ).length;

  return (
    <>
      <div className="border-b border-border p-4">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <ListTree className="h-4 w-4 text-primary" aria-hidden="true" />
          Mục lục tài liệu
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Chọn một mục để mở đúng trang và nguồn.
        </p>
      </div>

      <nav aria-label="Mục lục tài liệu" className="max-h-[calc(100vh-13rem)] overflow-y-auto p-3">
        {outline.length === 0 ? (
          <div className="px-4 py-10 text-center">
            <BookOpen className="mx-auto h-6 w-6 text-muted-foreground" aria-hidden="true" />
            <p className="mt-3 text-sm font-medium">Không tìm thấy tiêu đề</p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              MinerU chưa nhận diện heading cho tài liệu này.
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {outline.map((block) => (
              <button
                key={block.id}
                type="button"
                onClick={() => onNavigate(block)}
                className={`w-full rounded-md px-3 py-2.5 text-left transition-colors hover:bg-surface ${
                  block.block_type === "doc_title" ? "font-semibold" : "pl-6 font-medium"
                }`}
              >
                <span className="line-clamp-2 text-sm leading-5 text-foreground">
                  {block.text || "Tiêu đề không có nội dung"}
                </span>
                <span className="mt-1 block text-xs font-normal text-muted-foreground">
                  Trang {block.page_number}
                </span>
              </button>
            ))}
          </div>
        )}

        <details className="mt-4 rounded-lg border border-border bg-surface">
          <summary className="cursor-pointer px-3 py-3 text-sm font-medium">
            Kiểm tra dữ liệu trích xuất
          </summary>
          <dl className="grid grid-cols-2 gap-3 border-t border-border p-3 text-xs">
            <DebugMetric label="Trang có nội dung" value={pagesWithContent} />
            <DebugMetric label="Tổng block" value={blocks.length} />
            <DebugMetric label="Có geometry" value={geometryCount} />
            <DebugMetric label="Thiếu geometry" value={blocks.length - geometryCount} />
          </dl>
        </details>
      </nav>
    </>
  );
}

function SelectedBlockPanel({
  block,
  sourceEngine,
  onClose,
}: {
  block: DocumentPreviewBlock;
  sourceEngine: string | null;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timeout = window.setTimeout(() => setCopied(false), 1800);
    return () => window.clearTimeout(timeout);
  }, [copied]);

  async function copyText() {
    if (!block.text) return;
    await navigator.clipboard.writeText(block.text);
    setCopied(true);
  }

  return (
    <div className="flex max-h-[calc(100vh-4rem)] flex-col">
      <div className="flex items-start justify-between gap-3 border-b border-border p-4">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold">
            <FileSearch className="h-4 w-4 text-primary" aria-hidden="true" />
            Nguồn đang chọn
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Trang {block.page_number} · {formatBlockType(block.block_type)}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Đóng chi tiết block"
          className="grid h-8 w-8 place-items-center scanofy-control text-muted-foreground hover:bg-surface hover:text-foreground"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      <div className="overflow-y-auto p-4">
        <div className="rounded-lg border border-primary/20 bg-info-soft p-4">
          <p className="whitespace-pre-wrap text-base leading-7 text-foreground">
            {block.text || "Block này không chứa nội dung chữ."}
          </p>
        </div>

        <button
          type="button"
          onClick={() => void copyText()}
          disabled={!block.text}
          className="mt-3 inline-flex h-9 w-full items-center justify-center gap-2 scanofy-control border border-border text-sm font-medium transition-colors hover:bg-surface disabled:cursor-not-allowed disabled:opacity-40"
        >
          {copied ? (
            <Check className="h-4 w-4 text-success" aria-hidden="true" />
          ) : (
            <Clipboard className="h-4 w-4" aria-hidden="true" />
          )}
          {copied ? "Đã sao chép" : "Sao chép nội dung"}
        </button>

        <div className="mt-6">
          <p className="text-xs font-medium text-muted-foreground">Hành động học tập</p>
          <div className="mt-2 grid gap-2">
            <DeferredAction icon={Sparkles} label="Giải thích đoạn này" />
            <DeferredAction icon={Languages} label="Dịch nội dung" />
            <DeferredAction icon={MessageCircleQuestion} label="Tạo câu hỏi" />
          </div>
          <p className="mt-2 text-xs leading-5 text-muted-foreground">
            Các hành động AI sẽ được nối ở batch Learning; nguồn trang và block đã sẵn sàng.
          </p>
        </div>

        <dl className="mt-6 space-y-2 rounded-lg border border-border p-3 text-xs">
          <MetadataRow label="Engine" value={sourceEngine ?? block.source_engine ?? "—"} />
          <MetadataRow label="Reading order" value={block.reading_order?.toString() ?? "—"} />
          <MetadataRow label="Tọa độ" value={block.coordinate_system ?? "Không có"} />
        </dl>
      </div>
    </div>
  );
}

function DeferredAction({
  icon: Icon,
  label,
}: {
  icon: typeof Sparkles;
  label: string;
}) {
  return (
    <button
      type="button"
      disabled
      title="Sẽ có trong batch Learning"
      className="flex h-10 cursor-not-allowed items-center gap-3 scanofy-control border border-border px-3 text-sm text-muted-foreground opacity-60"
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
      {label}
    </button>
  );
}

function DebugMetric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-semibold text-foreground">{value}</dd>
    </div>
  );
}

function MetadataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="break-all text-right font-medium text-foreground">{value}</dd>
    </div>
  );
}

function formatBlockType(type: string): string {
  const labels: Record<string, string> = {
    title: "Tiêu đề tài liệu",
    heading: "Tiêu đề mục",
    paragraph: "Đoạn văn",
    doc_title: "Tiêu đề tài liệu",
    paragraph_title: "Tiêu đề mục",
    text: "Đoạn văn",
    image: "Hình ảnh",
    table: "Bảng",
    equation: "Công thức",
    page_number: "Số trang",
    header: "Đầu trang",
    footer: "Chân trang",
  };
  return labels[type] ?? type.replaceAll("_", " ");
}
