# Architecture

## 1. Request flow: React → API → Django → Business Logic → PostgreSQL

```
┌─────────────┐      HTTPS/JSON       ┌──────────────────────┐
│   React     │  ───────────────────> │  Django REST         │
│  (Vite SPA) │                       │  Framework            │
│             │ <─────────────────── │  (views/serializers)  │
└─────────────┘      JSON response    └──────────┬────────────┘
      │                                          │
      │ axios, JWT in                            │ calls into
      │ Authorization header                     ▼
      │                               ┌──────────────────────┐
      │                               │  Service layer         │
      │                               │  (validation.py,       │
      │                               │   matching.py,          │
      │                               │   services.py per app) │
      │                               └──────────┬────────────┘
      │                                          │ Django ORM
      │                                          ▼
      │                               ┌──────────────────────┐
      └── static assets ─────────────>│     PostgreSQL         │
          (dev: Vite; prod: served    └──────────────────────┘
           via WhiteNoise from Django)
```

- The **React SPA** never talks to PostgreSQL directly and holds no business logic beyond
  form validation and display formatting — every number on screen comes from an API response.
- **DRF views/viewsets** handle HTTP concerns (auth, permissions, serialization, pagination,
  filtering) and delegate anything with real logic to a **service module**
  (`apps/<app>/services.py`, `validation.py`, `matching.py`, `gateway.py`, `advice.py`). This
  keeps views thin and lets the same logic run from the seed command and the test suite
  without going through HTTP.
- **JWT (SimpleJWT)** is the only auth mechanism; every endpoint enforces permissions
  server-side via DRF permission classes (`apps/authentication/permissions.py`) — the
  frontend hiding a button is a UX nicety, never the security boundary.
- **Audit logging** is cross-cutting: `apps/audit_logs/services.log_action()` is called from
  every service function that performs a meaningful state change, and
  `AuditAwareJWTAuthentication` (a thin SimpleJWT subclass) stashes the authenticated user
  into a thread-local so audit entries are attributed correctly without threading `request`
  through every function signature.

## 2. Invoice pipeline: Upload → OCR → Extraction → Validation → PO Matching → Approval → Payment

```
 Upload                OCR                Field           Validation          PO Match
┌────────┐  store   ┌─────────┐  raw   ┌──────────┐ parse ┌──────────┐  rules ┌──────────┐
│ file(s)│ ───────> │ Invoice │ ─────> │ Tesseract│ ────> │ regex    │ ─────> │ mandatory │
│        │          │Document │  text  │ or demo  │ text  │ parsing  │ fields │ fields,   │
└────────┘          └─────────┘        │ fallback │       │(extraction│       │ GSTIN     │
                                        └─────────┘       │   .py)   │       │ format,   │
                                                           └──────────┘       │ amount    │
                                                                              │ math,     │
                                                                              │ duplicates│
                                                                              └────┬─────┘
                                                                                   │
                        ┌──────────────────────────────────────────────────────────┘
                        ▼
                 ┌─────────────┐   2-way / 3-way    ┌───────────────┐
                 │  PO Matching │ ────────────────> │ MATCHED /      │
                 │ (matching.py)│  vs PO + GRN qty   │ PARTIAL_MATCH /│
                 └─────┬───────┘                    │ MISMATCH       │
                       │                             └───────────────┘
                       │ no open exceptions
                       ▼
                ┌───────────────┐   amount-based    ┌────────────────┐
                │ Submit for     │ ────────────────> │ Sequential      │
                │ Approval       │   matrix lookup    │ Approval        │
                │ (create_       │                    │ Workflow        │
                │  workflow)     │                    │ (AP Manager →   │
                └───────────────┘                    │  Finance Mgr →  │
                                                       │  Admin, by band)│
                                                       └────────┬────────┘
                                                                │ all steps approved
                                                                ▼
                                                       ┌────────────────┐
                                                       │ Payment Request │
                                                       │ → Mock Banking  │
                                                       │   Gateway       │
                                                       │ → Payment Advice│
                                                       └────────────────┘
```

Each arrow in the diagram is a distinct, independently-callable service function and a
distinct `Invoice.status` value, so the state machine is always inspectable from the
database (`UPLOADED → PROCESSING → EXTRACTED → VALIDATED ⇄ EXCEPTION → PENDING_APPROVAL →
APPROVED → PAYMENT_PENDING → PAID`, with `REJECTED` reachable from the approval stage).

### Why OCR, extraction, and validation are three separate modules

| Module | Job | Never does |
|---|---|---|
| `apps/ocr/providers.py` | Get raw text off a document (or fall back honestly) | Understand what the text means |
| `apps/ocr/extraction.py` | Parse candidate field values out of raw text via regex | Judge whether they're *correct* |
| `apps/invoices/validation.py` | Enforce business rules against the invoice's current field values | Care where those values came from (OCR vs. manual edit) |

This separation is what makes "user manually corrects a field on the review screen, then
re-validation runs cleanly against the corrected value" work without special-casing —
validation only ever looks at the `Invoice` row's current state.

### Approval matrix

`ApprovalMatrixRule` rows (amount band → ordered list of required roles) are configurable at
`/api/approvals/matrix/` (Settings page in the UI, Admin/AP Manager only) rather than
hard-coded, per the spec's example bands:

- `< ₹50,000` → AP Manager
- `₹50,000 – ₹5,00,000` → AP Manager + Finance Manager
- `> ₹5,00,000` → AP Manager + Finance Manager + Admin

`apps/approvals/services.create_workflow()` resolves the applicable rule at submission time
and creates one `ApprovalStep` per required role, in order; `apply_action()` advances the
workflow sequentially on each approve/reject/request-changes decision.

### Exception handling and human overrides

`InvoiceException` rows are raised automatically by `validation.py` and `matching.py`, but a
human decision (resolve/reject/override, all requiring a comment) is authoritative:
re-running validation never silently reopens an exception a reviewer already disposed of —
see `_maybe_raise()` in `validation.py`.
