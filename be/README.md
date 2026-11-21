# Scanofy Backend

Week 1 backend scaffold for the Vietnamese Educational Document Intelligence System.

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

OCR, normalization, hierarchy building, RAG, and education features are placeholders only.

## MinerU Integration

Week 2 integrates MinerU through the `mineru` CLI instead of importing it into
the FastAPI process. Keep MinerU in a separate Python 3.10-3.12 environment on
Windows, then expose the `mineru` command on `PATH`.

```powershell
py -3.12 -m venv .venv-mineru
.\.venv-mineru\Scripts\activate
python -m pip install --upgrade pip
pip install uv
uv pip install -U "mineru[all]"
mineru --help
```

Configure the backend:

```env
MINERU_ENABLED=true
MINERU_COMMAND=mineru
MINERU_OUTPUT_DIR=storage/mineru_outputs
MINERU_BACKEND=pipeline
MINERU_TIMEOUT_SECONDS=900
```

For CPU-only machines, `pipeline` is the safest backend. Once the CLI is
available, PDF/DOCX uploads routed to MinerU are parsed, stored in
`ocr_outputs`, and minimally normalized into `pages` and `blocks`.
