# Foxtrail — Fraud Investigation Console

Premium React + TypeScript frontend for the Foxtrail agentic fraud investigation project.

## Run

```bash
npm install
npm run dev
```

Open `http://localhost:5173`.

## Pages

- Overview
- Investigation register
- Case detail workspace
- Investigation / Evidence / Decision / Report tabs
- Animated agent progression

## Backend integration

The frontend first attempts:

`/api/overview`

or, when `VITE_API_URL` is set:

`<VITE_API_URL>/api/overview`

If the API is unavailable, it automatically falls back to:

`/demo-overview.json`

Example `.env`:

```env
VITE_API_URL=http://localhost:8000
```

Adjust the API base URL to the port used by your existing Python/agent backend.

## Logo

`public/assets/fox-logo.png` and `public/assets/fox-favicon.png` are the supplied Foxtrail fox image.
