# AP Automation

An Accounts Payable automation platform: invoice capture → OCR extraction → validation →
duplicate detection → GST/tax validation → PO matching → approval workflows → vendor
management → payment request generation → payment tracking → reporting → audit logging →
dashboard analytics.

Built as a realistic enterprise SaaS product — not a CRUD demo. Every screen is backed by
real data from PostgreSQL via Django REST Framework; nothing in the UI is hard-coded.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [OCR Setup](#ocr-setup)
- [Running the App](#running-the-app)
- [Demo Credentials](#demo-credentials)
- [API Documentation](#api-documentation)
- [Roles & Permissions](#roles--permissions)
- [Testing](#testing)
- [Docker](#docker)
- [Architecture Decisions](#architecture-decisions)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)

## Overview

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the request flow and the invoice processing
pipeline in detail. The short version:

```
React (Vite) ── REST/JSON ──> Django REST Framework ──> Business logic services ──> PostgreSQL
```

The end-to-end demo flow (~8–12 minutes): Login → Dashboard → Upload Invoice → OCR
Extraction → Review/Edit → Validation → PO Matching → Exception Handling → Approval →
Vendor Profile → Payment Request → Payment Processing → Reports → Audit Logs.

## Tech Stack

- **Frontend:** React 19, Vite, React Router, Axios, Tailwind CSS v4, Recharts, Lucide icons
- **Backend:** Python 3.11, Django 5, Django REST Framework, SimpleJWT, django-cors-headers,
  django-filter, drf-spectacular
- **Database:** PostgreSQL 16
- **OCR:** Tesseract (via `pytesseract`) + `pdf2image`/Poppler for PDFs + OpenCV
  preprocessing, behind a provider abstraction (see [OCR Setup](#ocr-setup))

## Architecture

```
frontend/src/
  components/   reusable UI (ui/, layout/, invoices/, approvals/)
  pages/        one file per route
  layouts/      AppLayout (sidebar + navbar + outlet)
  services/     one file per API resource (axios wrappers)
  context/      AuthContext, ToastContext
  charts/       Recharts wrappers (validated color palette)
  utils/        navigation config, chart colors

backend/
  manage.py
  config/               settings, root urls, wsgi/asgi
  apps/
    common/             shared abstract models, seed_demo_data management command
    authentication/     custom User model + roles, JWT views, permissions
    vendors/            Vendor, VendorBankDetails, onboarding workflow
    purchase_orders/    PurchaseOrder, GoodsReceipt (GRN)
    invoices/           Invoice, OCR review, validation engine, exceptions, PO matching
    ocr/                OCR provider abstraction (Tesseract / demo fallback) + field parsing
    approvals/           approval matrix, workflow/step/action models + services
    payments/            payment requests, mock banking gateway, advice generation
    dashboard/, reports/ KPI + chart + CSV report aggregation
    audit_logs/          audit trail model, middleware, viewer
    notifications/       in-app notifications
```

Each Django app owns one business domain — no shared "god app". Business logic (validation,
matching, approval progression, payment simulation) lives in `services.py`/`validation.py`/
`matching.py` modules, not in views, so it's reusable from the API, the seed command, and
tests.

## Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- PostgreSQL 14+
- Tesseract OCR + Poppler (optional — the app falls back to a clearly-labeled demo extractor
  if these aren't installed; see [OCR Setup](#ocr-setup))

## Installation

### 1. Clone and set up PostgreSQL

```bash
sudo -u postgres psql -c "CREATE USER apuser WITH PASSWORD 'apuser_dev_pw';"
sudo -u postgres psql -c "CREATE DATABASE ap_automation OWNER apuser;"
```

### 2. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # edit if your DB credentials differ

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data --reset   # realistic demo data (see below)

python manage.py runserver               # http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                              # http://localhost:5173
```

The Vite dev server proxies `/api` and `/media` to `http://localhost:8000` (configurable via
`VITE_API_PROXY_TARGET`, used by Docker Compose).

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and adjust as needed:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key — generate a real one for anything beyond local dev |
| `DEBUG` | `True`/`False` |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `DATABASE_URL` | Optional single connection string (overrides the `DB_*` vars below) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection |
| `CORS_ALLOWED_ORIGINS` | Origins allowed to call the API (the Vite dev server by default) |
| `OCR_PROVIDER` | `tesseract` (default, falls back to `demo` automatically if Tesseract isn't installed) or `demo` to force the fallback |
| `OCR_API_KEY` | Reserved for a future cloud OCR provider (Textract/Document AI/Azure) — unused today |
| `MAX_UPLOAD_SIZE_MB` | Per-file upload size limit |

Never commit a real `.env` — it's gitignored. `.env.example` has no real secrets.

## OCR Setup

The OCR pipeline is a clean 3-stage abstraction (see `backend/apps/ocr/`):

1. **`providers.py`** — raw text extraction. `TesseractOCRProvider` does *real* OCR
   (pytesseract + pdf2image for PDFs + OpenCV preprocessing). If Tesseract isn't installed,
   `DemoOCRProvider` engages automatically as a clearly-labeled fallback — it does **not**
   read the document and never claims a real result (`ocr_provider: "demo"` is always visible
   in the API/UI).
2. **`extraction.py`** — regex-based field parsing over the raw text (invoice number, GSTIN,
   dates, amounts, vendor name). Decoupled from OCR so it's independently testable.
3. **`service.py`** — orchestrates the two stages, computes per-field and overall confidence
   (average of successfully-extracted *mandatory* fields), and persists the result.

Install Tesseract for real OCR:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler
```

Without it, the app still works end-to-end for a demo — extraction just falls back to manual
entry on the review screen, exactly as it would for a real low-confidence scan.

## Running the App

With Postgres running and both dev servers up:

1. Open `http://localhost:5173`
2. Log in with a [demo account](#demo-credentials)
3. Follow the demo flow from the Dashboard: Upload → OCR review → Validate → PO Match →
   resolve any exceptions → Submit for Approval → Approve → Raise Payment Request → Process
   Payment → check Reports/Audit Logs

## Demo Credentials

Created by `python manage.py seed_demo_data`:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@12345` |
| AP Manager | `ap.manager` | `Demo@12345` |
| AP Processor | `ap.processor` | `Demo@12345` |
| Approver | `approver` | `Demo@12345` |
| Finance Manager | `finance.manager` | `Demo@12345` |
| Auditor | `auditor` | `Demo@12345` |

The seed command also creates 10 vendors, purchase orders with GRNs, and 30+ invoices
covering every required demo scenario: valid/matched, duplicate (exact + near), amount
mismatch, missing PO, low OCR confidence, invalid GSTIN, pending/partial/fully-approved,
rejected, and paid. Re-run with `--reset` any time to restore a clean demo state.

## API Documentation

Interactive Swagger UI: `http://localhost:8000/api/docs/`
Raw OpenAPI schema: `http://localhost:8000/api/schema/`

Key endpoint groups: `/api/auth/`, `/api/invoices/`, `/api/exceptions/`,
`/api/purchase-orders/`, `/api/approvals/` (+ `/api/approvals/matrix/`), `/api/vendors/`,
`/api/payments/`, `/api/dashboard/`, `/api/reports/`, `/api/audit-logs/`,
`/api/notifications/`.

## Roles & Permissions

Enforced **server-side** on every endpoint (never just by hiding a button in the UI):

- **Admin** — full access, final approval tier, audit logs
- **AP Manager** — vendor management, invoice processing, first-tier approvals, approval
  matrix configuration
- **AP Processor** — invoice upload/review, exception handling
- **Approver** — approves assigned steps
- **Finance Manager** — second-tier approvals, payment processing
- **Auditor** — read-only, audit log access

## Testing

Backend (Django `APITestCase`, 39 tests covering auth, upload, validation, duplicate
detection, PO matching, approval workflow, vendor management, payment workflow, and
permissions):

```bash
cd backend
source venv/bin/activate
python manage.py test apps
```

Frontend (Vitest + Testing Library, component behavior + the API error-parsing utility):

```bash
cd frontend
npm test
```

## Docker

```bash
docker compose up --build
```

Starts Postgres, the Django backend (migrates automatically on boot), and the Vite dev
server. First run: `docker compose exec backend python manage.py seed_demo_data --reset`.
Local (non-Docker) setup works identically and doesn't depend on Docker in any way.

## Architecture Decisions

- **UUID primary keys** everywhere for security (non-guessable IDs) and eventual multi-region
  friendliness.
- **Service-layer functions**, not fat views/serializers, for anything with real business
  logic (validation, matching, approval progression, payment simulation) — reused by the API,
  the seed command, and the tests.
- **JWT in `sessionStorage`**, not `localStorage` — clears on tab close, a small hardening
  step over the more common `localStorage` pattern (see [Known Limitations](#known-limitations)
  for what a fuller hardening would look like).
- **OCR provider abstraction** so a real cloud OCR service can be swapped in later by adding
  one class, without touching extraction, validation, or any UI code.
- **Synchronous OCR/validation/matching on upload**, not a background task queue — appropriate
  for demo-scale files and keeps the stack simple to run locally without Redis/Celery. See
  Future Improvements for the production path.
- **Every "simulated" system is labeled as such in the API response and the UI** — the mock
  banking gateway and the demo OCR fallback both carry explicit flags so a reader is never
  misled into thinking a real integration ran.

## Known Limitations

- OCR field-parsing uses regex heuristics tuned for common English-language Indian tax
  invoice layouts; it will need per-format tuning for wildly different invoice templates.
- Payment processing is a **mock gateway only** — no real bank/NEFT/RTGS integration. It's
  clearly labeled as simulated everywhere (API responses, UI banners, generated advice).
- GST validation checks **GSTIN format only** (a standard regex) — there is no live
  government GSTIN verification API integration.
- OCR/validation/PO-matching run synchronously in the request/response cycle. This is fine at
  demo scale but would need to move to a background worker (Celery/RQ) for large files or
  high upload volume in production.
- "Avg. Processing Time" and the processing-trend chart are most meaningful once invoices
  accumulate real elapsed time between pipeline stages; freshly-seeded demo data was all
  created in one batch, so those two data points look flatter than they would after a few
  days of real usage.
- No end-to-end (Cypress/Playwright) test suite is checked into the repo, though the full
  demo flow was manually verified in a real browser during development.

## Future Improvements

- Background task queue (Celery + Redis) for OCR/validation/matching on large files
- Real cloud OCR provider (AWS Textract / Google Document AI / Azure Document Intelligence)
  as a second `BaseOCRProvider` implementation
- Real banking/payment gateway integration behind the existing `MockBankingGateway` interface
- S3-backed file storage (the storage layer is already abstracted via Django's `FileField`)
- Live GSTIN verification against the GST Network API
- WebSocket/SSE push for notifications instead of client polling
- httpOnly-cookie-based auth instead of `sessionStorage` JWTs, for full XSS hardening
