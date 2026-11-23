"use client";

import {
  ChangeEvent,
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { AlertCircle, Library, RefreshCw } from "lucide-react";

import { DocumentList } from "@/components/library/document-list";
import { ProcessingPanel } from "@/components/library/processing-panel";
import { UploadPanel } from "@/components/library/upload-panel";
import { AppSidebar } from "@/components/shell/app-sidebar";
import { isTerminalDocumentStatus } from "@/lib/document-ui";
import {
  getDocumentStatus,
  listDocuments,
  uploadDocument,
} from "@/lib/api";
import type {
  DocumentRecord,
  DocumentStatusResponse,
} from "@/types/documents";

export function LibraryWorkspace() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [activeDocument, setActiveDocument] = useState<DocumentRecord | null>(null);
  const [activeStatus, setActiveStatus] = useState<DocumentStatusResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const status = activeStatus?.status ?? activeDocument?.status ?? "idle";
  const readyCount = useMemo(
    () =>
      documents.filter((document) =>
        ["parsed", "completed"].includes(document.status),
      ).length,
    [documents],
  );
  const failedCount = useMemo(
    () => documents.filter((document) => document.status === "failed").length,
    [documents],
  );

  const refreshDocuments = useCallback(async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      setDocuments(await listDocuments());
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể tải danh sách tài liệu.",
      );
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void refreshDocuments(), 0);
    return () => window.clearTimeout(timeout);
  }, [refreshDocuments]);

  useEffect(() => {
    if (!activeDocument || isTerminalDocumentStatus(status)) return;

    const interval = window.setInterval(async () => {
      try {
        const current = await getDocumentStatus(activeDocument.id);
        setActiveStatus(current);
        setActiveDocument((document) =>
          document ? { ...document, status: current.status } : document,
        );
        setDocuments((items) =>
          items.map((document) =>
            document.id === current.document_id
              ? { ...document, status: current.status }
              : document,
          ),
        );
      } catch (reason) {
        setError(
          reason instanceof Error
            ? reason.message
            : "Không thể cập nhật trạng thái.",
        );
      }
    }, 1500);

    return () => window.clearInterval(interval);
  }, [activeDocument, status]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setError(null);
    setSelectedFile(event.target.files?.[0] ?? null);
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);
    try {
      const result = await uploadDocument(selectedFile);
      setActiveDocument(result.document);
      setActiveStatus({
        document_id: result.document.id,
        status: result.document.status,
        profile: result.document.profile,
        router_decision: result.document.router_decision,
        latest_job: result.job,
      });
      setSelectedFile(null);
      await refreshDocuments();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Tải tài liệu thất bại.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function selectDocument(document: DocumentRecord) {
    setActiveDocument(document);
    setError(null);
    try {
      const current = await getDocumentStatus(document.id);
      setActiveStatus(current);
      setActiveDocument({ ...document, status: current.status });
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể mở trạng thái tài liệu.",
      );
    }
  }

  return (
    <div className="min-h-screen bg-background lg:grid lg:grid-cols-[248px_minmax(0,1fr)]">
      <AppSidebar />

      <div className="min-w-0">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-4 border-b border-border bg-background/95 px-4 backdrop-blur sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary text-sm font-semibold text-primary-foreground lg:hidden">
              S
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">Thư viện</p>
              <p className="hidden text-xs text-muted-foreground sm:block">
                Tài liệu của tôi / Tiếp nhận
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => void refreshDocuments()}
            disabled={isRefreshing}
            className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-border bg-background px-3 text-sm font-medium text-foreground transition-colors hover:bg-surface disabled:opacity-50"
          >
            <RefreshCw
              className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
              aria-hidden="true"
            />
            <span className="hidden sm:inline">Làm mới</span>
          </button>
        </header>

        <main className="px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <div className="mx-auto max-w-[1420px]">
            <div className="flex flex-col justify-between gap-5 border-b border-border pb-6 sm:flex-row sm:items-end">
              <div>
                <div className="flex items-center gap-2 text-sm font-medium text-primary">
                  <Library className="h-4 w-4" aria-hidden="true" />
                  Không gian tài liệu
                </div>
                <h1 className="mt-2 text-2xl font-semibold leading-8 tracking-tight">
                  Biến tài liệu thành kiến thức có thể học
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                  Tải lên tài liệu giáo dục, theo dõi quá trình phân tích và luôn
                  giữ liên kết với nguồn gốc.
                </p>
              </div>
              <div className="flex items-center gap-5 text-sm">
                <Summary label="Tổng cộng" value={documents.length} />
                <Summary label="Sẵn sàng" value={readyCount} />
                <Summary
                  label="Cần xem"
                  value={failedCount}
                  danger={failedCount > 0}
                />
              </div>
            </div>

            {error && (
              <div
                role="alert"
                aria-live="assertive"
                className="mt-5 flex items-start justify-between gap-4 rounded-lg border border-danger/20 bg-danger-soft p-4 text-sm text-danger"
              >
                <div className="flex items-start gap-3">
                  <AlertCircle
                    className="mt-0.5 h-4 w-4 shrink-0"
                    aria-hidden="true"
                  />
                  <span>{error}</span>
                </div>
              </div>
            )}

            <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
              <div className="space-y-6">
                <UploadPanel
                  selectedFile={selectedFile}
                  isUploading={isUploading}
                  onFileChange={handleFileChange}
                  onSubmit={handleUpload}
                />
                <ProcessingPanel
                  document={activeDocument}
                  status={activeStatus}
                />
              </div>
              <DocumentList
                documents={documents}
                activeDocumentId={activeDocument?.id}
                isLoading={isRefreshing}
                onSelect={(document) => void selectDocument(document)}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function Summary({
  label,
  value,
  danger = false,
}: {
  label: string;
  value: number;
  danger?: boolean;
}) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p
        className={`mt-1 font-semibold ${
          danger ? "text-danger" : "text-foreground"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
