# Scanofy

**Vietnamese Educational Document Intelligence System**

Scanofy is an AI-powered document processing system that converts Vietnamese educational PDFs, DOCX files, scans, and handwritten images into structured, searchable, and learning-ready content.

The project is not just an OCR wrapper. Its main goal is to build a complete **Document Intelligence pipeline**: upload a document, route it to the most suitable OCR/parser engine, normalize multi-engine outputs into a unified schema, reconstruct a hierarchical educational document tree, and generate learning features such as summaries, Q&A, flashcards, and quizzes.

## Quick start

Requirements: Python 3.11 and Node.js 20.9 or newer.

Backend, from the repository root:

```powershell
cd be
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Frontend, in another terminal from the repository root:

```powershell
cd fe
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

The frontend is available at `http://localhost:3000`; the backend API and
OpenAPI documentation are at `http://127.0.0.1:8000` and `/docs`. To run the
current backend tests plus frontend lint/build checks:

```powershell
.\scripts\check.ps1
```

---

## 1. Project Vision

Students and teachers often work with many types of learning materials:

- Digital PDFs with text layers
- DOCX documents
- Scanned PDFs
- Photos of printed pages
- Handwritten images
- Documents containing tables, math formulas, exercises, and answers

A normal OCR system only extracts plain text. Scanofy aims to go further by understanding the **structure** of educational documents.

The final system should answer questions such as:

- What chapters and lessons exist in this document?
- Which section contains the definition of a concept?
- Where are the exercises and answers?
- Which formulas appear in a lesson?
- Can this lesson be summarized?
- Can flashcards or quizzes be generated from this section?
- Can answers be grounded back to the original page/block?

---

## 2. Core Idea

The system uses a **quality-aware document router** instead of forcing all documents through one OCR engine.

```text
Input: PDF / DOCX / Image / Scan / Handwriting
        |
        v
File Profiler
- detect file type
- detect text layer
- detect scan quality
- detect handwriting probability
- estimate layout complexity
- estimate Vietnamese content
        |
        v
OCR / Parser Router
        |
        |-- Digital PDF / DOCX / text-layer document
        |       -> MinerU
        |       -> Markdown + JSON + LaTeX formulas + HTML tables
        |
        |-- Scan / image / handwritten / no text layer
        |       -> Chandra OCR 2
        |       -> structured text + layout
        |
        |-- Low-confidence / Vietnamese-heavy / noisy result
                -> Vintern-1B fallback
                -> correction or repair
        |
        v
Unified Document Schema
        |
        v
Vietnamese Post-correction
        |
        v
Layout & Reading Order Refinement
        |
        v
Hierarchy Builder
        |
        v
Education Feature Engine
```

---

## 3. Why This Project Is Different

This project should not be described as a simple OCR application.

The novelty is in these parts:

1. **Quality-aware OCR routing**  
   The system chooses the best parser/OCR engine based on file type, text-layer ratio, scan score, handwriting probability, language score, layout complexity, and confidence.

2. **Multi-engine output normalization**  
   MinerU, Chandra OCR, and Vintern-1B may return different output formats. Scanofy converts them into one unified document schema.

3. **Vietnamese-focused post-correction**  
   The system includes a controlled LLM correction module for Vietnamese diacritics, spacing, and OCR errors while preserving the original meaning.

4. **Educational hierarchy reconstruction**  
   Instead of returning plain text, the system builds a semantic document tree:
   chapters, lessons, sections, theory, examples, exercises, answers, formulas, tables, and figures.

5. **Source-grounded learning features**  
   Summaries, Q&A, flashcards, and quizzes are generated from specific document tree nodes and can be traced back to original pages and blocks.

---

## 4. Target Users

Primary target users:

- Vietnamese students
- Teachers
- Tutors
- Self-learners
- People who want to digitize educational materials

Possible use cases:

- Convert scanned learning materials into structured notes
- Extract exercises and answers from documents
- Ask questions based on uploaded documents
- Generate flashcards from a specific lesson
- Summarize a chapter or section
- Build a searchable personal study library

---

## 5. Tech Stack

### Frontend

```text
Next.js
TypeScript
TailwindCSS
shadcn/ui
PDF.js
React Flow or tree-view component
```

Frontend responsibilities:

- Upload documents
- Show processing status
- Preview original PDF/image
- Show extracted Markdown/text
- Show document tree
- Show Q&A, summaries, flashcards, and quizzes
- Show source citations such as page number and block id

---

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

Backend responsibilities:

- File upload API
- Job creation and processing
- File profiling
- OCR/parser routing
- Calling OCR adapters
- Output normalization
- Document tree construction
- RAG and education feature APIs

---

### Database

```text
Neon Postgres
PostgreSQL JSONB
pgvector
```

Why Neon Postgres:

- Cloud-native and easy to deploy
- Good for relational data
- JSONB can store raw OCR outputs
- pgvector can support RAG in the MVP stage
- Suitable for document metadata, pages, blocks, tree nodes, chunks, and embeddings

---

### Object Storage

```text
Cloudflare R2
or AWS S3
or Supabase Storage
```

Used for:

- Original uploaded files
- Generated page images
- Markdown outputs
- JSON outputs
- HTML tables
- LaTeX formula outputs

---

### Queue / Cache

```text
Redis
Upstash Redis for cloud deployment
```

Used for:

- Background OCR jobs
- Processing status
- Async task queue
- Temporary caching

---

### OCR / Document AI Engines

```text
MinerU
Chandra OCR 2
Vintern-1B
LLM post-correction
Embedding model for RAG
```

Expected usage:

- **MinerU**: Digital PDFs, DOCX files, text-layer documents
- **Chandra OCR 2**: Scanned PDFs, images, handwriting, layout-heavy pages
- **Vintern-1B**: Vietnamese-heavy fallback, noisy handwriting, low-confidence OCR
- **LLM**: Vietnamese correction, hierarchy refinement, education feature generation

---

### Deployment

```text
Frontend: Vercel
Backend: Render / Railway / Fly.io
Database: Neon
Redis: Upstash
Storage: Cloudflare R2
```

---

## 6. High-Level Architecture

```text
┌──────────────────┐
│     Frontend     │
│ Next.js + PDF.js │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│   FastAPI API    │
│ Upload / Status  │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│   Object Storage │
│ R2 / S3          │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│  Background Job  │
│ Celery / RQ      │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│  File Profiler   │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ OCR/Parser Router│
└────────┬─────────┘
         │
         ├───────────────┐
         │               │
         v               v
┌────────────────┐ ┌────────────────┐
│ MinerU Adapter │ │ Chandra Adapter│
└────────────────┘ └────────────────┘
         │               │
         └───────┬───────┘
                 v
        ┌──────────────────┐
        │ Unified Normalizer│
        └────────┬─────────┘
                 v
        ┌──────────────────┐
        │ Post-correction  │
        └────────┬─────────┘
                 v
        ┌──────────────────┐
        │ Hierarchy Builder│
        └────────┬─────────┘
                 v
        ┌──────────────────┐
        │ Education Engine │
        └────────┬─────────┘
                 v
        ┌──────────────────┐
        │ Neon Postgres    │
        │ JSONB + pgvector │
        └──────────────────┘
```

---

## 7. Main Pipeline

### Step 1: Upload Document

Supported input types:

```text
.pdf
.docx
.png
.jpg
.jpeg
.webp
```

The backend creates a document record and a processing job.

Initial document status:

```text
uploaded -> queued -> processing -> completed / failed
```

---

### Step 2: File Profiling

The File Profiler extracts metadata and quality signals.

Example output:

```json
{
  "file_type": "pdf",
  "page_count": 12,
  "has_text_layer": true,
  "text_layer_ratio": 0.86,
  "scan_score": 0.12,
  "handwriting_score": 0.03,
  "layout_complexity_score": 0.41,
  "vietnamese_score": 0.91,
  "route_hint": "mineru"
}
```

Possible profiling features:

- file type
- file size
- page count
- text layer ratio
- image density
- scan score
- handwriting probability
- Vietnamese language score
- table/formula density
- layout complexity score

---

### Step 3: OCR / Parser Routing

Router logic example:

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

Fallback logic:

```python
def should_use_fallback(result):
    if result.average_confidence < 0.80:
        return True

    if result.vietnamese_error_score > 0.35:
        return True

    if result.layout_failure_score > 0.40:
        return True

    return False
```

---

### Step 4: OCR / Parser Adapter

Each engine should be wrapped by an adapter.

Expected interface:

```python
class BaseOCRAdapter:
    def parse(self, file_path: str) -> dict:
        raise NotImplementedError
```

Adapters:

```text
services/ocr_engines/mineru_adapter.py
services/ocr_engines/chandra_adapter.py
services/ocr_engines/vintern_adapter.py
```

All adapters should return a consistent intermediate format.

Example:

```json
{
  "engine": "mineru",
  "markdown": "# Bài 1: Hàm số\n...",
  "pages": [],
  "blocks": [],
  "tables": [],
  "formulas": [],
  "raw_output": {}
}
```

---

### Step 5: Unified Document Schema

All OCR/parser outputs must be normalized into a shared schema.

Example block:

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

### Step 6: Layout and Reading Order Refinement

This step improves the raw OCR output.

Tasks:

- Remove repeated headers
- Remove footers
- Remove page numbers
- Merge broken paragraphs
- Split mixed blocks
- Sort blocks by reading order
- Detect question numbering
- Detect answer sections
- Preserve tables and formulas

Example question patterns:

```text
Câu 1.
Bài 2.
1)
a)
A.
I.
II.
1.1
```

---

### Step 7: Vietnamese Post-correction

The LLM post-correction module should be controlled and conservative.

It is allowed to:

- Restore Vietnamese diacritics
- Fix obvious OCR errors
- Fix spacing errors
- Normalize punctuation
- Repair broken words

It must not:

- Add new knowledge
- Rewrite the meaning
- Change numbers
- Change formulas
- Change names if uncertain
- Hallucinate missing content

Example output:

```json
{
  "block_id": "p2_b8",
  "original_text": "phuong trinh bac hai",
  "corrected_text": "phương trình bậc hai",
  "edit_type": "diacritic_restoration",
  "confidence": 0.95,
  "needs_review": false
}
```

---

### Step 8: Hierarchy Builder

The hierarchy builder converts flat blocks into an educational document tree.

Target structure:

```text
Document
 ├── Chapter
 │    ├── Lesson
 │    │    ├── Theory
 │    │    ├── Example
 │    │    ├── Exercise
 │    │    ├── Answer
 │    │    ├── Formula
 │    │    └── Table
```

Supported node types:

```text
document
chapter
lesson
section
subsection
theory
example
exercise
answer
formula
table
figure
unknown
```

Rule-based detection examples:

```text
"Chương 1" -> chapter
"Bài 2" -> lesson
"I.", "II." -> section
"1.", "1.1" -> subsection
"Ví dụ" -> example
"Bài tập", "Câu 1" -> exercise
"Đáp án", "Lời giải" -> answer
```

The hierarchy builder can start rule-based, then later be improved using LLM refinement.

---

### Step 9: Chunking and Embedding

Chunks should be generated from tree nodes, not arbitrary fixed-size text only.

Chunking strategy:

```text
chapter -> lesson -> section -> block group
```

Each chunk should keep source metadata:

```json
{
  "chunk_id": "chunk_001",
  "document_id": "doc_001",
  "node_id": "node_014",
  "page_start": 3,
  "page_end": 4,
  "block_ids": ["p3_b2", "p3_b3", "p4_b1"],
  "text": "...",
  "embedding": []
}
```

This enables source-grounded Q&A.

---

### Step 10: Education Feature Engine

Features should be generated from document tree nodes.

MVP features:

1. **Section Summary**
   - Summarize a chapter, lesson, or section.
   - Avoid summarizing the entire document at once.

2. **Q&A with Citation**
   - Answer questions using RAG.
   - Return source page, block id, and node id.

3. **Flashcard Generator**
   - Generate flashcards from a selected lesson or section.

4. **Quiz Generator**
   - Generate multiple-choice, true/false, or short-answer questions.

Optional future features:

- Exercise extractor
- Answer extractor
- Formula explainer
- Learning path generator
- Weak concept detector
- Anki export
- Markdown export
- JSON export

---

## 8. Database Schema Draft

### documents

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    user_id UUID NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    storage_url TEXT NOT NULL,
    status TEXT NOT NULL,
    router_decision JSONB,
    profile JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### document_jobs

```sql
CREATE TABLE document_jobs (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    current_step TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### ocr_outputs

```sql
CREATE TABLE ocr_outputs (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    engine TEXT NOT NULL,
    raw_output JSONB,
    markdown_output TEXT,
    average_confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### pages

```sql
CREATE TABLE pages (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    page_number INT NOT NULL,
    width FLOAT,
    height FLOAT,
    image_url TEXT,
    raw_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### blocks

```sql
CREATE TABLE blocks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    page_id UUID REFERENCES pages(id),
    page_number INT NOT NULL,
    block_type TEXT NOT NULL,
    text TEXT,
    corrected_text TEXT,
    bbox JSONB,
    reading_order INT,
    confidence FLOAT,
    correction_confidence FLOAT,
    needs_review BOOLEAN DEFAULT FALSE,
    source_engine TEXT,
    raw_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### document_tree_nodes

```sql
CREATE TABLE document_tree_nodes (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    parent_id UUID NULL REFERENCES document_tree_nodes(id),
    node_type TEXT NOT NULL,
    title TEXT,
    content TEXT,
    page_start INT,
    page_end INT,
    block_ids JSONB,
    level INT,
    order_index INT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### chunks

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    node_id UUID REFERENCES document_tree_nodes(id),
    text TEXT NOT NULL,
    page_start INT,
    page_end INT,
    block_ids JSONB,
    embedding VECTOR,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### generated_features

```sql
CREATE TABLE generated_features (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    node_id UUID NULL REFERENCES document_tree_nodes(id),
    feature_type TEXT NOT NULL,
    content JSONB NOT NULL,
    source_chunk_ids JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 9. API Draft

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

### Evaluation

```text
GET /documents/{document_id}/evaluation
GET /evaluation/summary
```

---

## 10. Suggested Folder Structure

```text
scanofy/
 ├── be/
 │   ├── app/
 │   │   ├── main.py
 │   │   ├── api/
 │   │   │   ├── routes_documents.py
 │   │   │   ├── routes_tree.py
 │   │   │   ├── routes_features.py
 │   │   │   └── routes_evaluation.py
 │   │   ├── core/
 │   │   │   ├── config.py
 │   │   │   ├── security.py
 │   │   │   └── logging.py
 │   │   ├── db/
 │   │   │   ├── session.py
 │   │   │   └── base.py
 │   │   ├── models/
 │   │   ├── schemas/
 │   │   ├── services/
 │   │   │   ├── document_processing.py
 │   │   │   ├── hierarchy_builder.py
 │   │   │   ├── chunking.py
 │   │   │   └── education_features.py
 │   │   ├── workers/
 │   │   │   ├── celery_app.py
 │   │   │   └── tasks.py
 │   │   └── utils/
 │   ├── alembic/
 │   ├── tests/
 │   ├── requirements.txt
 │   ├── Dockerfile
 │   └── docker-compose.yml
 │
 ├── fe/
 │   ├── app/
 │   │   ├── page.tsx
 │   │   ├── documents/
 │   │   └── evaluation/
 │   ├── components/
 │   │   ├── upload/
 │   │   ├── document-viewer/
 │   │   ├── tree-viewer/
 │   │   ├── markdown-viewer/
 │   │   └── features/
 │   ├── lib/
 │   ├── types/
 │   ├── package.json
 │   └── next.config.ts
 │
 ├── ai/
 │   ├── adapters/
 │   │   ├── mineru.py
 │   │   ├── paddleocr.py
 │   │   ├── chandra.py
 │   │   └── vintern.py
 │   ├── profiling/
 │   ├── normalization/
 │   ├── post_correction/
 │   ├── evaluation/
 │   ├── tests/
 │   └── README.md
 │
 ├── sample_documents/
 │   ├── digital_pdf/
 │   ├── scanned_pdf/
 │   ├── docx/
 │   ├── handwriting/
 │   ├── math_formula/
 │   └── table_heavy/
 │
 ├── docs/
 │   ├── architecture.md
 │   ├── database.md
 │   ├── pipeline.md
 │   └── evaluation.md
 │
 ├── README.md
 └── .env.example
```

---

## 11. Environment Variables

Example `.env`:

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
VINTERn_ENABLED=false

APP_ENV=development
```

---

## 12. 8-Week Development Roadmap

### Week 1: Foundation

Goal:

```text
FastAPI + Neon + upload + job status
```

Tasks:

- Setup backend project
- Setup frontend project
- Connect Neon Postgres
- Add SQLAlchemy models and Alembic
- Implement upload API
- Store uploaded files
- Create document and job records
- Show status on frontend

Deliverable:

```text
Upload file -> database record -> job status visible in UI
```

---

### Week 2: File Router + MinerU

Goal:

```text
Digital PDF/DOCX -> MinerU -> Markdown/JSON
```

Tasks:

- Implement File Profiler
- Implement OCR Router
- Implement MinerU adapter
- Store raw OCR output
- Show extracted Markdown

Deliverable:

```text
Upload PDF/DOCX -> router chooses MinerU -> output Markdown/JSON
```

---

### Week 3: Chandra/Vintern Branch

Goal:

```text
Image/scan/handwriting -> Chandra OCR -> structured output
```

Tasks:

- Implement Chandra adapter
- Add Vintern adapter placeholder
- Add fallback architecture
- Store raw output
- Add manual rerun endpoint

Deliverable:

```text
Upload image/scan -> router chooses Chandra -> structured text/layout
```

---

### Week 4: Unified Schema + MVP Viewer

Goal:

```text
Multi-engine outputs -> normalized blocks -> document viewer
```

Tasks:

- Implement normalizer
- Insert pages and blocks into database
- Build document detail page
- Show Markdown
- Show block list
- Show router decision
- Show processing timeline

Deliverable:

```text
MVP v1: upload -> route -> parse -> normalize -> view result
```

---

### Week 5: Vietnamese Post-correction

Goal:

```text
Improve Vietnamese OCR quality
```

Tasks:

- Implement post-correction service
- Fix diacritics
- Fix spacing
- Preserve formulas/numbers
- Add correction confidence
- Mark low-confidence blocks for review
- Add layout refinement rules

Deliverable:

```text
OCR text -> corrected Vietnamese text with confidence and review flags
```

---

### Week 6: Hierarchy Builder

Goal:

```text
Flat blocks -> educational document tree
```

Tasks:

- Implement rule-based hierarchy builder
- Detect chapter, lesson, section, exercise, answer, formula, table
- Store tree nodes
- Add tree viewer UI
- Connect tree node to source blocks

Deliverable:

```text
Document tree visible in UI
```

---

### Week 7: Education Features

Goal:

```text
Generate learning features from document tree
```

Tasks:

- Implement chunking by tree node
- Generate embeddings
- Store embeddings in pgvector
- Implement RAG question answering
- Implement section summary
- Implement flashcards
- Implement quiz generation
- Return source citations

Deliverable:

```text
User can summarize, ask questions, generate flashcards and quizzes from a selected node
```

---

### Week 8: Evaluation + Deploy + Polish

Goal:

```text
CV-ready project
```

Tasks:

- Add evaluation dashboard
- Prepare sample documents
- Measure processing time/page
- Measure block count and confidence
- Measure correction count
- Add README screenshots
- Deploy `fe`/`be` và AI inference service khi cần
- Polish GitHub documentation
- Prepare CV bullets

Deliverable:

```text
Deployed demo + GitHub README + evaluation page + CV-ready description
```

---

## 13. MVP Scope

The MVP should focus on:

```text
1. Upload PDF/DOCX/image
2. Route to suitable OCR/parser
3. Extract Markdown/JSON/text/layout
4. Normalize into pages and blocks
5. Build basic document tree
6. Generate summary and flashcards from one tree node
```

Do not over-focus on UI polish early. The first goal is to make the pipeline work end-to-end.

---

## 14. Future Improvements

Possible future work:

- Better handwriting detection
- Better table structure recognition
- Formula-level RAG
- Human review UI for low-confidence blocks
- OCR comparison mode between engines
- Automatic answer extraction from exercise documents
- Anki export
- PDF highlight source viewer
- Teacher dashboard
- Student learning progress tracking
- Multi-document knowledge base
- Hybrid search using keyword + vector search
- Move vector search from pgvector to Qdrant Cloud if needed

---

## 15. CV Positioning

Do not describe this project as:

```text
OCR app
```

Better description:

```text
Vietnamese Educational Document Intelligence System
```

Suggested CV bullet:

```text
Built a Vietnamese educational document intelligence system that routes PDFs, DOCX files, scans, and handwritten images to suitable OCR/parser engines, normalizes multi-engine outputs into a unified document schema, reconstructs hierarchical document trees, and generates source-grounded learning features such as summaries, Q&A, flashcards, and quizzes.
```

Technical contribution bullets:

```text
- Designed a quality-aware OCR router using file type, text-layer ratio, scan score, handwriting probability, layout complexity, Vietnamese language score, and confidence signals.
- Integrated MinerU for digital PDF/DOCX parsing and Chandra OCR/Vintern-1B fallback for scanned or Vietnamese-heavy documents.
- Built a unified schema for text blocks, layout bounding boxes, tables, formulas, reading order, confidence scores, and source-engine metadata.
- Developed a Vietnamese LLM post-correction module for OCR error correction and diacritic restoration while preserving original meaning.
- Implemented a hierarchy builder that converts raw document content into educational structures such as chapters, lessons, sections, exercises, answers, tables, and formulas.
- Added RAG-based educational features with page/block-level source grounding.
```

---

## 16. First Coding Tasks for Codex

Start with the following tasks in order:

1. Create monorepo folder structure.
2. Create FastAPI backend.
3. Add `.env.example`.
4. Add SQLAlchemy database connection.
5. Add Alembic migration setup.
6. Create models:
   - Document
   - DocumentJob
   - OCROutput
   - Page
   - Block
   - DocumentTreeNode
   - Chunk
   - GeneratedFeature
7. Implement upload endpoint.
8. Implement document status endpoint.
9. Implement placeholder background processing job.
10. Implement File Profiler stub.
11. Implement Router stub.
12. Implement OCR adapter base class.
13. Implement MinerU adapter placeholder.
14. Implement Chandra adapter placeholder.
15. Implement Normalizer placeholder.

The first milestone should be:

```text
Upload a document and see its processing status in the UI.
```

---

## 17. Current Priority

Current development priority:

```text
Week 1
Backend foundation + Neon Postgres + upload + job queue + status tracking
```

Do not start with advanced OCR before the upload/job/database foundation is stable.
