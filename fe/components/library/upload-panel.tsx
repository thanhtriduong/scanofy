import { ChangeEvent, FormEvent } from "react";
import { FileText, Loader2, Upload } from "lucide-react";

import { formatBytes } from "@/lib/document-ui";

type UploadPanelProps = {
  selectedFile: File | null;
  isUploading: boolean;
  onFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function UploadPanel({
  selectedFile,
  isUploading,
  onFileChange,
  onSubmit,
}: UploadPanelProps) {
  return (
    <form
      onSubmit={onSubmit}
      className="rounded-lg border border-border bg-surface-raised p-5"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold leading-7">Tải tài liệu lên</h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Scanofy sẽ phân tích cấu trúc và giữ liên kết với file gốc.
          </p>
        </div>
        <Upload className="h-5 w-5 text-primary" aria-hidden="true" />
      </div>

      <label
        htmlFor="document-upload"
        className="mt-5 flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-border-strong bg-surface px-5 py-8 text-center transition-colors hover:border-primary hover:bg-info-soft"
      >
        <span className="grid h-11 w-11 place-items-center rounded-lg border border-border bg-surface-raised text-muted-foreground">
          <FileText className="h-5 w-5" aria-hidden="true" />
        </span>
        <span className="mt-3 text-sm font-medium text-foreground">
          {selectedFile ? selectedFile.name : "Chọn tài liệu từ máy"}
        </span>
        <span className="mt-1 text-xs text-muted-foreground">
          {selectedFile
            ? formatBytes(selectedFile.size)
            : "PDF, DOCX, JPG, PNG hoặc WEBP · tối đa 50 MB"}
        </span>
        <input
          id="document-upload"
          className="sr-only"
          type="file"
          accept=".pdf,.docx,.jpg,.jpeg,.png,.webp"
          onChange={onFileChange}
        />
      </label>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          File gốc luôn được giữ lại để đối chiếu nguồn.
        </p>
        <button
          type="submit"
          disabled={!selectedFile || isUploading}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-45"
        >
          {isUploading ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Upload className="h-4 w-4" aria-hidden="true" />
          )}
          {isUploading ? "Đang tải lên" : "Tải lên"}
        </button>
      </div>
    </form>
  );
}
