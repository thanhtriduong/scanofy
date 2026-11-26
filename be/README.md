# Scanofy Backend

Backend for the Vietnamese Educational Document Intelligence System.

## Runtime

- Python 3.11
- Environment file: `be/.env`
- Local tests use an isolated in-memory SQLite database and never use Neon.

## Run Locally

```bash
cd be
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Use `DATABASE_URL` for Neon Postgres. For quick local smoke tests, set:

```env
DATABASE_URL=sqlite:///./scanofy_dev.db
```

Run the backend checks:

```powershell
python -m pytest
```

## Week 1 Endpoints

- `GET /health`
- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/status`
- `DELETE /documents/{document_id}`

MinerU parsing and Page/Block/Span normalization are operational;
hierarchy building, RAG, and education features remain placeholders.

## MinerU Integration

MinerU 4.2.3 is invoked through its local `mineru-kit` CLI. It may be installed
in the backend virtual environment when a single environment is preferred.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-mineru.txt
.\.venv\Scripts\mineru-kit.exe parse --help
```

Configure the backend:

```env
MINERU_ENABLED=true
MINERU_COMMAND=mineru-kit
MINERU_OUTPUT_DIR=storage/mineru_outputs
MINERU_OCR_MODE=auto
MINERU_TIMEOUT_SECONDS=900
```

The adapter uses local parsing with automatic OCR mode and exports a ZIP that
contains Markdown, middle JSON, structured JSON, and image assets. PDF/DOCX
uploads routed to MinerU are parsed, stored in
`ocr_outputs`, and normalized into `pages`, `blocks`, and `spans`.

Each parse retains its own artifacts, source hash and CLI version. Missing or
invalid output fails explicitly; the original document remains readable.
See [MinerU pipeline and recovery commands](../docs/MINERU_PIPELINE.md) for
supported artifacts, API access, renormalization, real smoke tests and diagrams.
