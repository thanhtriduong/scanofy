# Scanofy

**Vietnamese Educational Document Intelligence System**

Scanofy is an AI personal project that converts Vietnamese PDFs, DOCX files, scanned documents, and handwritten images into structured educational content.

The project is not only an OCR app. It is a document intelligence pipeline that:

1. Uploads a PDF, DOCX, image, scan, or handwriting file.
2. Routes the file to the most suitable OCR/parser.
3. Normalizes outputs from different engines into one schema.
4. Corrects Vietnamese OCR errors.
5. Builds a hierarchical educational document tree.
6. Generates learning features such as summaries, Q&A, flashcards, and quizzes.

---

## 1. Main Goal

Build a cloud-ready AI system for Vietnamese educational documents.

The system should transform raw files into:

- Markdown
- JSON
- pages
- layout blocks
- tables
- formulas
- document tree
- RAG-ready chunks
- learning features

Example final tree:

```text
Document
├── Chapter 1
│   ├── Lesson 1
│   │   ├── Theory
│   │   ├── Example
│   │   ├── Exercise
│   │   └── Answer
│   └── Lesson 2
└── Chapter 2
```

---

## 2. Why This Project Is Different

Do not describe this project as a simple OCR tool.

The important parts are:

- quality-aware OCR routing
- multi-engine OCR/parser integration
- unified document schema
- Vietnamese post-correction
- educational hierarchy builder
- source-grounded education features

The value is not only extracting text, but converting documents into structured learning materials.

---

## 3. OCR / Parser Strategy

```text
Input file
   |
   v
File Profiler
   |
   v
Router
   |
   |-- PDF/DOCX with text layer
   |      -> MinerU
   |
   |-- Scan/image/handwriting/no text layer
   |      -> Chandra OCR 2
   |
   |-- Low confidence or Vietnamese-heavy noisy result
          -> Vintern-1B fallback
```

Expected engine usage:

| Case | Engine |
|---|---|
| Digital PDF | MinerU |
| DOCX | MinerU |
| PDF with text layer | MinerU |
| Scanned PDF | Chandra OCR 2 |
| Image/photo | Chandra OCR 2 |
| Handwritten image | Chandra OCR 2 or Vintern-1B |
| Low-confidence Vietnamese result | Vintern-1B fallback |

---

## 4. Tech Stack

### Frontend

```text
Next.js
TypeScript
TailwindCSS
shadcn/ui
PDF.js
React Flow or tree-view component
```

### Backend

```text
Python
FastAPI
SQLAlchemy
Alembic
Celery or RQ
Redis
Pydantic
```

### Database

```text
Neon Postgres
JSONB
pgvector
```

### Storage

```text
Cloudflare R2 or AWS S3-compatible storage
```

### Queue / Cache

```text
Redis or Upstash Redis
```

### AI / OCR

```text
MinerU
Chandra OCR 2
Vintern-1B
LLM post-correction
Embedding model for RAG
```

### Deployment

```text
Frontend: Vercel
Backend: Render / Railway / Fly.io
Database: Neon
Redis: Upstash
Storage: Cloudflare R2
```

---

## 5. System Pipeline

```text
Upload document
   |
   v
Create document record
   |
   v
Create background job
   |
   v
File profiler
   |
   v
OCR/parser router
   |
   v
OCR/parser adapter
   |
   v
Raw OCR output
   |
   v
Unified normalizer
   |
   v
Pages + blocks
   |
   v
Vietnamese post-correction
   |
   v
Layout refinement
   |
   v
Hierarchy builder
   |
   v
Chunking + embeddings
   |
   v
Education features
```

---

## 6. Core Services

Backend services should be separated like this:

```text
services/
├── file_profiler.py
├── router.py
├── normalizer.py
├── post_correction.py
├── layout_refinement.py
├── hierarchy_builder.py
├── chunking.py
├── embeddings.py
├── rag.py
├── education_features.py
└── ocr_engines/
    ├── base.py
    ├── mineru_adapter.py
    ├── chandra_adapter.py
    └── vintern_adapter.py
```

---

## 7. Unified Block Schema

All OCR engines must be normalized into this structure:

```json
{
  "block_id": "p1_b5",
  "document_id": "doc_001",
  "page_number": 1,
  "type": "paragraph",
  "text": "Phương trình bậc hai có dạng ax^2 + bx + c = 0.",
  "bbox": [100, 120, 700, 180],
  "reading_order": 5,
  "confidence": 0.91,
  "source_engine": "mineru",
  "raw_ref": {}
}
```

Supported block types:

```text
title
heading
paragraph
table
formula
image
caption
question
answer
list
unknown
```

---

## 8. Router Logic Draft

```python
def choose_engine(profile):
    if profile.file_type in ["pdf", "docx"] and profile.text_layer_ratio >= 0.6:
        return "mineru"

    if profile.file_type in ["jpg", "jpeg", "png", "webp"]:
        return "chandra"

    if profile.scan_score >= 0.5 or profile.handwriting_score >= 0.4:
        return "chandra"

    return "mineru_with_fallback"
```

Fallback rule:

```python
def should_use_fallback(result):
    return (
        result.average_confidence < 0.80
        or result.vietnamese_error_score > 0.35
        or result.layout_failure_score > 0.40
    )
```

---

## 9. Database Tables

Main tables:

```text
documents
document_jobs
ocr_outputs
pages
blocks
document_tree_nodes
chunks
generated_features
```

### documents

Stores uploaded document metadata.

Fields:

```text
id
user_id
filename
file_type
storage_url
status
profile JSONB
router_decision JSONB
created_at
updated_at
```

### document_jobs

Stores background processing state.

Fields:

```text
id
document_id
job_type
status
current_step
error_message
started_at
finished_at
created_at
```

### ocr_outputs

Stores raw OCR/parser result.

Fields:

```text
id
document_id
engine
raw_output JSONB
markdown_output
average_confidence
created_at
```

### pages

Stores page-level data.

Fields:

```text
id
document_id
page_number
width
height
image_url
raw_text
created_at
```

### blocks

Stores normalized layout/text blocks.

Fields:

```text
id
document_id
page_id
page_number
block_type
text
corrected_text
bbox JSONB
reading_order
confidence
correction_confidence
needs_review
source_engine
raw_json JSONB
created_at
```

### document_tree_nodes

Stores educational hierarchy.

Fields:

```text
id
document_id
parent_id
node_type
title
content
page_start
page_end
block_ids JSONB
level
order_index
created_at
```

### chunks

Stores RAG chunks.

Fields:

```text
id
document_id
node_id
text
page_start
page_end
block_ids JSONB
embedding VECTOR
metadata JSONB
created_at
```

### generated_features

Stores generated summaries, flashcards, quizzes, etc.

Fields:

```text
id
document_id
node_id
feature_type
content JSONB
source_chunk_ids JSONB
created_at
```

---

## 10. API Draft

### Documents

```text
POST   /documents/upload
GET    /documents
GET    /documents/{document_id}
GET    /documents/{document_id}/status
DELETE /documents/{document_id}
```

### Processing

```text
POST /documents/{document_id}/process
POST /documents/{document_id}/rerun
POST /documents/{document_id}/rerun?engine=mineru
POST /documents/{document_id}/rerun?engine=chandra
POST /documents/{document_id}/rerun?engine=vintern
```

### OCR Output

```text
GET /documents/{document_id}/ocr-output
GET /documents/{document_id}/blocks
GET /documents/{document_id}/pages
```

### Document Tree

```text
GET  /documents/{document_id}/tree
GET  /documents/{document_id}/nodes/{node_id}
POST /documents/{document_id}/build-tree
```

### Education Features

```text
POST /documents/{document_id}/nodes/{node_id}/summary
POST /documents/{document_id}/nodes/{node_id}/flashcards
POST /documents/{document_id}/nodes/{node_id}/quiz
POST /documents/{document_id}/ask
```

---

## 11. Folder Structure

```text
scanofy/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── workers/
│   │   └── utils/
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── types/
│   └── package.json
│
├── sample_documents/
├── docs/
├── README.md
└── .env.example
```

---

## 12. Environment Variables

```env
DATABASE_URL=postgresql://user:password@host/dbname
REDIS_URL=redis://localhost:6379

OBJECT_STORAGE_ENDPOINT=
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=
OBJECT_STORAGE_BUCKET=

OPENAI_API_KEY=
GOOGLE_API_KEY=
HF_TOKEN=

MINERU_ENABLED=true
CHANDRA_ENABLED=true
VINTERN_ENABLED=false

APP_ENV=development
```

---

## 13. 8-Week Timeline

| Week | Goal |
|---|---|
| Week 1 | FastAPI + Neon + upload + job status |
| Week 2 | File profiler + router + MinerU |
| Week 3 | Chandra branch + Vintern fallback placeholder |
| Week 4 | Unified schema + document viewer MVP |
| Week 5 | Vietnamese post-correction + layout refinement |
| Week 6 | Hierarchy builder + tree viewer |
| Week 7 | RAG + summary + flashcard + quiz |
| Week 8 | Evaluation + deploy + README polish |

---

## 14. MVP Scope

MVP should include:

```text
1. Upload PDF/DOCX/image
2. Save file and metadata
3. Create processing job
4. Route document to OCR/parser
5. Extract text/Markdown/JSON
6. Normalize pages and blocks
7. Build simple document tree
8. Generate summary and flashcards from one node
```

Do not implement all advanced features at the beginning.

---

## 15. Current Priority for Codex

Codex should start with Week 1 only.

Implement:

1. Monorepo folder structure
2. FastAPI backend
3. `.env.example`
4. SQLAlchemy database connection
5. Alembic migration setup
6. Models:
   - Document
   - DocumentJob
   - OCROutput
   - Page
   - Block
   - DocumentTreeNode
   - Chunk
   - GeneratedFeature
7. Upload endpoint
8. Document status endpoint
9. Placeholder background processing job
10. File Profiler stub
11. Router stub
12. OCR adapter base class
13. MinerU adapter placeholder
14. Chandra adapter placeholder
15. Normalizer placeholder

First milestone:

```text
Upload a document and see its processing status in the UI.
```

---

## 16. CV Positioning

Suggested project title:

```text
Vietnamese Educational Document Intelligence System
```

Suggested CV bullet:

```text
Built a Vietnamese educational document intelligence system that routes PDFs, DOCX files, scans, and handwritten images to suitable OCR/parser engines, normalizes multi-engine outputs into a unified document schema, reconstructs hierarchical document trees, and generates source-grounded learning features such as summaries, Q&A, flashcards, and quizzes.
```
