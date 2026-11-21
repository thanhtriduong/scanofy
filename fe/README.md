# Scanofy frontend

Next.js interface for uploading documents and tracking the Scanofy processing
pipeline.

## Requirements

- Node.js 20.9 or newer (`.nvmrc` currently records Node.js 24.21.0)
- The backend running at the URL configured in `.env.local`

## Run locally

```powershell
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Verify

```powershell
npm run lint
npm run build
```
