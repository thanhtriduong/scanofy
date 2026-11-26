"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FileText, Plus, RefreshCw, Trash2 } from "lucide-react";
import { AppSidebar } from "@/components/shell/app-sidebar";
import { UploadPanel } from "@/components/library/upload-panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { deleteDocument, listDocuments, uploadDocument } from "@/lib/api";
import { formatDocumentDate } from "@/lib/document-ui";
import type { DocumentRecord } from "@/types/documents";

export function LibraryWorkspace() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [showUpload, setShowUpload] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function removeDocument(doc: DocumentRecord) {
    if (!window.confirm(`Xóa “${doc.filename}”? File gốc, kết quả phân tích và dữ liệu liên quan sẽ bị xóa vĩnh viễn.`)) return;
    setDeletingId(doc.id);
    try {
      await deleteDocument(doc.id);
      setDocuments((current) => current.filter((item) => item.id !== doc.id));
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể xóa tài liệu.");
    } finally { setDeletingId(null); }
  }
  const refresh = useCallback(async () => {
    try { setDocuments(await listDocuments()); setError(null); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể tải thư viện."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    const initial = window.setTimeout(() => void refresh(), 0);
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => { window.clearTimeout(initial); window.clearInterval(timer); };
  }, [refresh]);

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || uploading) return;
    setUploading(true); setError(null);
    try {
      const result = await uploadDocument(file);
      router.push(`/documents/${result.document.id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải tài liệu lên.");
      setUploading(false);
    }
  }
  const visible = documents.filter((doc) =>
    doc.filename.toLocaleLowerCase().includes(query.toLocaleLowerCase()) &&
    (filter === "all" || (filter === "ready" ? ["parsed", "completed"].includes(doc.status) : filter === "failed" ? doc.status === "failed" : !["parsed", "completed", "failed"].includes(doc.status))),
  );

  return (
    <div className="min-h-screen bg-background lg:grid lg:grid-cols-[248px_minmax(0,1fr)]">
      <AppSidebar />
      <main className="min-w-0 px-4 py-8 sm:px-8">
        <div className="mx-auto max-w-6xl">
          <header className="flex flex-wrap items-center justify-between gap-4">
            <div><h1 className="text-2xl font-medium">Thư viện tài liệu</h1><p className="mt-2 text-sm text-muted-foreground">Mở tài liệu để tiếp tục đọc, khám phá và học.</p></div>
            <button type="button" onClick={() => setShowUpload(!showUpload)} aria-expanded={showUpload} className="scanofy-control inline-flex h-10 items-center gap-2 bg-primary px-5 text-sm font-medium text-primary-foreground hover:bg-primary-hover"><Plus className="h-4 w-4" />Tải tài liệu lên</button>
          </header>
          {error && <p role="alert" className="mt-5 rounded-lg bg-danger-soft p-4 text-sm text-danger">{error}</p>}
          {showUpload && <div className="mt-6" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); if (!uploading) setFile(event.dataTransfer.files[0] ?? null); }}>
            <UploadPanel selectedFile={file} isUploading={uploading} onFileChange={(event) => setFile(event.target.files?.[0] ?? null)} onSubmit={upload} />
          </div>}
          <div className="my-6 flex flex-wrap items-end gap-3">
            <label className="min-w-48 flex-1 text-xs text-muted-foreground">Tìm tài liệu<input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm theo tên tài liệu" className="mt-2 block h-10 w-full rounded-full border bg-background px-4 text-sm text-foreground" /></label>
            <label className="text-xs text-muted-foreground">Trạng thái<select value={filter} onChange={(event) => setFilter(event.target.value)} className="mt-2 block h-10 rounded-full border bg-background px-4 text-sm text-foreground"><option value="all">Tất cả</option><option value="ready">Đã phân tích</option><option value="pending">Chờ phân tích</option><option value="failed">Phân tích lỗi</option></select></label>
            <button type="button" aria-label="Làm mới thư viện" onClick={() => void refresh()} className="scanofy-control grid h-10 w-10 place-items-center border hover:bg-surface"><RefreshCw className="h-4 w-4" /></button>
          </div>
          <div className="overflow-hidden rounded-lg border">
            {loading ? <p role="status" className="p-8 text-sm text-muted-foreground">Đang tải thư viện…</p> : visible.length === 0 ? <div className="p-12 text-center"><FileText className="mx-auto h-6 w-6 text-muted-foreground" /><p className="mt-3 text-sm">{documents.length ? "Không có tài liệu phù hợp." : "Thêm tài liệu đầu tiên để bắt đầu đọc."}</p></div> : visible.map((doc) => (
              <div key={doc.id} className="flex items-center gap-3 border-b px-5 py-4 last:border-b-0 hover:bg-surface">
              <Link href={`/documents/${doc.id}`} className="flex min-w-0 flex-1 flex-wrap items-center gap-4">
                <FileText className="h-5 w-5 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{doc.filename}</p><p className="mt-1 text-xs text-muted-foreground">{formatDocumentDate(doc.updated_at)} · {doc.file_type.toUpperCase()}</p></div>
                <StatusBadge status={doc.status} /><span className="text-sm text-primary">Mở tài liệu</span>
              </Link>
              <button type="button" aria-label={`Xóa ${doc.filename}`} disabled={deletingId !== null || ["uploaded", "queued", "processing", "normalizing"].includes(doc.status)} onClick={() => void removeDocument(doc)} className="scanofy-control grid h-10 w-10 shrink-0 place-items-center text-muted-foreground hover:bg-danger-soft hover:text-danger disabled:cursor-not-allowed disabled:opacity-40"><Trash2 className={`h-4 w-4 ${deletingId === doc.id ? "animate-pulse" : ""}`} aria-hidden="true" /></button>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
