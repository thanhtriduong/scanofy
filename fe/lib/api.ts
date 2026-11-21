import type {
  DocumentRecord,
  DocumentStatusResponse,
  UploadResponse,
} from "@/types/documents";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail ?? message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return request<UploadResponse>("/documents/upload", {
    method: "POST",
    body: formData,
  });
}

export async function getDocumentStatus(
  documentId: string,
): Promise<DocumentStatusResponse> {
  return request<DocumentStatusResponse>(`/documents/${documentId}/status`, {
    cache: "no-store",
  });
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  return request<DocumentRecord[]>("/documents", {
    cache: "no-store",
  });
}
