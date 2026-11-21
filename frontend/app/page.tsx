"use client";

import {
  AlertCircle,
  CheckCircle2,
  Database,
  FileText,
  Loader2,
  RefreshCw,
  Route,
  Upload,
} from "lucide-react";
import {
  ChangeEvent,
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getDocumentStatus,
  listDocuments,
  uploadDocument,
} from "@/lib/api";
import type {
  DocumentRecord,
  DocumentStatusResponse,
  UploadResponse,
} from "@/types/documents";

const terminalStatuses = new Set(["awaiting_ocr", "parsed", "completed", "failed"]);

function formatBytes(bytes?: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function statusTone(status: string) {
  if (status === "failed") return "border-red-200 bg-red-50 text-red-700";
  if (status === "awaiting_ocr" || status === "parsed" || status === "completed") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  if (status === "processing" || status === "uploaded") {
    return "border-blue-200 bg-blue-50 text-blue-700";
  }
  return "border-slate-200 bg-slate-50 text-slate-700";
}

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [activeStatus, setActiveStatus] = useState<DocumentStatusResponse | null>(null);
  const [activeDocument, setActiveDocument] = useState<DocumentRecord | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = Boolean(selectedFile) && !isUploading;
  const status = activeStatus?.status ?? activeDocument?.status ?? "idle";
  const latestJob = activeStatus?.latest_job;

  const acceptedTypes = useMemo(
    () => ".pdf,.docx,.jpg,.jpeg,.png,.webp",
    [],
  );

  const refreshDocuments = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await listDocuments();
      setDocuments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load documents.");
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void refreshDocuments();
    }, 0);

    return () => window.clearTimeout(timeout);
  }, [refreshDocuments]);

  useEffect(() => {
    if (!activeDocument || terminalStatuses.has(status)) return;

    const interval = window.setInterval(async () => {
      try {
        const current = await getDocumentStatus(activeDocument.id);
        setActiveStatus(current);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not refresh status.");
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
      const result: UploadResponse = await uploadDocument(selectedFile);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load status.");
    }
  }

  return (
    <main className="min-h-screen bg-[#f7f8fb] text-slate-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-5 py-6 lg:px-8">
        <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 md:flex-row md:items-end">
          <div>
            <p className="text-sm font-medium text-teal-700">Scanofy</p>
            <h1 className="mt-1 text-3xl font-semibold tracking-normal text-slate-950">
              Document intake workspace
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Upload Vietnamese educational documents and watch the Week 1
              processing state from FastAPI and Neon.
            </p>
          </div>
          <button
            type="button"
            onClick={refreshDocuments}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 text-sm font-medium text-slate-800 shadow-sm transition hover:bg-slate-50 disabled:opacity-60"
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </header>

        {error && (
          <div className="flex items-start gap-3 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-6">
            <form
              onSubmit={handleUpload}
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Upload document</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    PDF, DOCX, JPG, PNG, or WEBP. OCR is intentionally deferred.
                  </p>
                </div>
                <Upload className="h-5 w-5 text-teal-700" />
              </div>

              <label className="mt-5 flex cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center transition hover:border-teal-500 hover:bg-teal-50/60">
                <FileText className="h-9 w-9 text-slate-500" />
                <span className="mt-3 text-sm font-medium text-slate-900">
                  {selectedFile ? selectedFile.name : "Choose a document"}
                </span>
                <span className="mt-1 text-xs text-slate-500">
                  {selectedFile ? formatBytes(selectedFile.size) : "Up to the backend limit"}
                </span>
                <input
                  className="sr-only"
                  type="file"
                  accept={acceptedTypes}
                  onChange={handleFileChange}
                />
              </label>

              <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs text-slate-500">
                  Status will update automatically after upload.
                </p>
                <button
                  type="submit"
                  disabled={!canSubmit}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-teal-700 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {isUploading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Upload className="h-4 w-4" />
                  )}
                  Upload
                </button>
              </div>
            </form>

            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Processing status</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Active document pipeline state from the backend.
                  </p>
                </div>
                <span
                  className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${statusTone(status)}`}
                >
                  {status}
                </span>
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-3">
                <div className="rounded-md border border-slate-200 p-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
                    <Database className="h-4 w-4 text-teal-700" />
                    Record
                  </div>
                  <p className="mt-3 break-all text-sm text-slate-950">
                    {activeDocument?.filename ?? "No document selected"}
                  </p>
                </div>
                <div className="rounded-md border border-slate-200 p-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
                    <Route className="h-4 w-4 text-teal-700" />
                    Router
                  </div>
                  <p className="mt-3 text-sm text-slate-950">
                    {activeStatus?.router_decision?.engine ?? "Pending"}
                  </p>
                </div>
                <div className="rounded-md border border-slate-200 p-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
                    <CheckCircle2 className="h-4 w-4 text-teal-700" />
                    Job
                  </div>
                  <p className="mt-3 text-sm text-slate-950">
                    {latestJob?.current_step ?? "Idle"}
                  </p>
                </div>
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <pre className="min-h-40 overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-5 text-slate-100">
                  {JSON.stringify(activeStatus?.profile ?? {}, null, 2)}
                </pre>
                <pre className="min-h-40 overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-5 text-slate-100">
                  {JSON.stringify(activeStatus?.router_decision ?? {}, null, 2)}
                </pre>
              </div>
            </section>
          </div>

          <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">Recent documents</h2>
            <div className="mt-4 space-y-3">
              {documents.length === 0 ? (
                <p className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">
                  No uploads yet.
                </p>
              ) : (
                documents.map((document) => (
                  <button
                    key={document.id}
                    type="button"
                    onClick={() => selectDocument(document)}
                    className={`w-full rounded-md border p-3 text-left transition hover:border-teal-500 hover:bg-teal-50/50 ${
                      activeDocument?.id === document.id
                        ? "border-teal-500 bg-teal-50/70"
                        : "border-slate-200 bg-white"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <span className="min-w-0 truncate text-sm font-medium text-slate-950">
                        {document.filename}
                      </span>
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium uppercase text-slate-600">
                        {document.file_type}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center justify-between gap-3 text-xs text-slate-500">
                      <span>{document.status}</span>
                      <span>{new Date(document.created_at).toLocaleString()}</span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
