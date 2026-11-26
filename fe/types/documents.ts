export type DocumentRecord = {
  id: string;
  user_id: string | null;
  filename: string;
  file_type: string;
  storage_url: string;
  status: string;
  profile: FileProfile | null;
  router_decision: RouterDecision | null;
  created_at: string;
  updated_at: string;
};

export type DocumentJob = {
  id: string;
  document_id: string;
  job_type: string;
  status: string;
  current_step: string | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

export type FileProfile = {
  file_type: string;
  size_bytes: number;
  text_layer_ratio: number;
  scan_score: number;
  handwriting_score: number;
  page_count: number | null;
};

export type RouterDecision = {
  engine: string;
  reason: string;
  fallback_engine: string | null;
};

export type UploadResponse = {
  document: DocumentRecord;
  job: DocumentJob;
};

export type DocumentStatusResponse = {
  document_id: string;
  status: string;
  profile: FileProfile | null;
  router_decision: RouterDecision | null;
  latest_job: DocumentJob | null;
};

export type DocumentPreviewPage = {
  page_number: number;
  width: number | null;
  height: number | null;
  raw_text: string | null;
};

export type DocumentPreviewBlock = {
  id: string;
  parse_run_id?: string | null;
  heading_level?: number | null;
  page_number: number;
  block_type: string;
  text: string | null;
  bbox: number[] | null;
  reading_order: number | null;
  confidence: number | null;
  source_engine: string | null;
  coordinate_system: string | null;
};

export type DocumentPreviewResponse = {
  document: DocumentRecord;
  pages: DocumentPreviewPage[];
  blocks: DocumentPreviewBlock[];
  source_engine: string | null;
  parse_run_id?: string | null;
};
