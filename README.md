<div align="center">

# YieldStream Qualify

**Document Intelligence API for Automated MCA Underwriting**

[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?style=flat-square&logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=flat-square&logo=terraform&logoColor=white)](https://terraform.io)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)

*Extracts structured financial data from bank statements, tax returns, and MCA documents — then computes 25+ risk indicators for automated decisioning. One POST request replaces 15-30 minutes of manual underwriting.*

[Architecture](#architecture) &bull; [API Reference](#api-reference) &bull; [Getting Started](#getting-started) &bull; [Design Decisions](#design-decisions)

</div>

---

## The Problem

MCA underwriters manually review hundreds of bank statements and tax documents per week. Each review means opening PDFs, pulling numbers into spreadsheets, and computing metrics like average daily balance, NSF frequency, and existing MCA stacking burden.

**YieldStream Qualify reduces that to a single API call.** Upload a document, get back structured data with confidence scores and risk flags — ready for decisioning.

---

## Architecture

```
POST /parse/upload
        │
        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Quality Gate                                 │
│              blur | skew | contrast | resolution | photo detection   │
│                    rejects garbage early, saves compute              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ pass
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Extraction Orchestrator                           │
│                                                                      │
│  Tier 1: pdfplumber ──▶ Tier 2: PyMuPDF ──▶ Tier 3: Tesseract OCR  │
│                   (fastest, free)       (scanned)        (degraded)  │
│                                                    ──▶ Tier 4: LlamaParse │
│                                                         (cloud, last resort) │
│                                                                      │
│  Each tier is timed. Escalation is automatic when quality < threshold │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ text + tables
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Classification Engine                           │
│           keyword matching ──▶ structural patterns ──▶ Gemini LLM   │
│                        (fallback when confidence < 0.5)              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ document_type
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
   ┌─────────────────┐ ┌────────────┐ ┌──────────────────┐
   │ Bank Statement   │ │ Tax Return │ │  MCA Document    │
   │ Parser           │ │ Parser     │ │  Parser          │
   │                  │ │            │ │                  │
   │ 14 bank-specific │ │ 1120/1120S │ │ Applications +   │
   │ templates +      │ │ 1065/SchC  │ │ Approval Letters │
   │ generic fallback │ │ 1040       │ │ regex + LLM      │
   └────────┬─────────┘ └────────────┘ └──────────────────┘
            │
            ▼
   ┌──────────────────┐
   │ Enrichment Engine │
   │                   │
   │ 25+ risk metrics  │
   │ Gemini 2.0 Flash  │
   │ 15 RPM rate limit │
   └──────────────────┘
            │
            ▼
   ParseResponse { status, parsed_data, confidence, tier_logs, enrichment }
```

### Pipeline at a Glance

| Stage | What it does | Key detail |
|---|---|---|
| **Quality Gate** | Pre-flight image analysis | Rejects blurry/skewed docs before wasting extraction compute |
| **Extraction** | Cascading 4-tier text + table extraction | Auto-fallback with per-tier timing logs |
| **Classification** | Document type identification | Regex-first, Gemini only when confidence < 0.5 |
| **Parsing** | Type-specific structured extraction | Template registry scores 14 bank formats via thread-safe match history |
| **Enrichment** | Financial intelligence computation | Revenue trends, DSCR, NSF windows, MCA stacking, anomaly flags |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend** | Python 3.12, FastAPI, Pydantic v2 | Async-first, schema-driven validation, auto-generated OpenAPI docs |
| **Frontend** | React 19, TypeScript 6, Vite 8, Tailwind CSS 4 | Modern SPA with TanStack Query for server state |
| **PDF Extraction** | pdfplumber, PyMuPDF, Tesseract OCR, LlamaParse | Cascading tiers balance speed, cost, and document quality |
| **AI/LLM** | Google Gemini 2.0 Flash Lite | Classification fallback + financial enrichment with token-bucket rate limiting |
| **Infrastructure** | AWS Lambda (512 MB), API Gateway v2, ECR, CloudWatch | Serverless — scales to zero, pay-per-invocation |
| **IaC** | Terraform | Reproducible infrastructure, version-controlled state |
| **Testing** | pytest, pytest-asyncio, reportlab | Synthetic PDF generation for deterministic test fixtures |
| **Containerization** | Docker, docker-compose | Lambda-compatible images + local dev parity |

---

## API Reference

### Parse a Document

```bash
curl -X POST https://your-api.com/parse/upload \
  -F "file=@statement.pdf" \
  -F "include_enrichment=true" \
  -F "business_name=Acme Corp" \
  -F "industry=retail"
```

<details>
<summary><strong>Response structure</strong></summary>

```json
{
  "status": "success",
  "classification": {
    "document_type": "bank_statement",
    "confidence": 0.97,
    "method": "template_match"
  },
  "parsed_data": {
    "bank_name": "Chase",
    "account_number": "****4521",
    "statement_period": { "start": "2024-01-01", "end": "2024-01-31" },
    "opening_balance": 24531.82,
    "closing_balance": 31208.45,
    "total_deposits": 89420.00,
    "total_withdrawals": 82743.37,
    "transactions": [ "..." ],
    "derived_metrics": {
      "average_daily_balance": 27865.14,
      "negative_balance_days": 0,
      "nsf_count": 0
    }
  },
  "enrichment": {
    "revenue": { "monthly_average": 89420, "trend": "stable", "volatility_pct": 8.2 },
    "risk_flags": { "mca_stacking_detected": false, "dscr": 1.85 },
    "needs_human_review": false
  },
  "metadata": {
    "extraction_tier": "pdfplumber",
    "extraction_time_ms": 342,
    "confidence": { "overall": 0.94, "text_quality": 0.98, "template_match": 0.97 }
  },
  "tier_logs": [
    { "tier": "pdfplumber", "status": "success", "time_ms": 342, "chars_extracted": 12847 }
  ]
}
```

</details>

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Extractor availability check |
| `POST` | `/parse` | Parse document from URL |
| `POST` | `/parse/upload` | Parse uploaded file (multipart) |
| `POST` | `/classify` | Classify document type only |
| `POST` | `/extract-approval` | MCA approval letter terms (upload) |
| `POST` | `/extract-approval/url` | MCA approval letter terms (URL) |
| `POST` | `/v1/enrich` | Standalone financial enrichment |
| `GET` | `/review/queue` | Human review queue |
| `GET` | `/templates/bank` | Bank template metadata |

> Interactive API docs available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when running locally.

---

## Supported Documents

### Bank Statements — 14 Templates

Chase &bull; Bank of America &bull; Wells Fargo &bull; PNC &bull; US Bank &bull; Capital One &bull; Regions &bull; Truist &bull; Citizens &bull; Fifth Third &bull; BMO Harris &bull; Navy Federal Credit Union &bull; TD Bank &bull; **Generic Fallback**

Each template extracts account summaries, individual transactions with categorization, derived metrics (ADB, negative balance days, largest transactions), NSF/overdraft detection, and MCA payment identification.

### Tax Returns

| Form | Entity Type |
|---|---|
| 1120 | C-Corporation |
| 1120S | S-Corporation |
| 1065 | Partnership |
| Schedule C | Sole Proprietorship |
| 1040 | Personal |

### MCA Documents

- **Applications** — Business details, funding amount, owner info, existing debt positions
- **Approval Letters** — Offer terms, factor rates, payment schedules, stipulations, expiration

---

## Enrichment Engine

When `include_enrichment=true`, the API computes **25+ financial indicators** via Gemini:

| Category | Metrics |
|---|---|
| **Revenue** | Monthly average, trend direction, volatility %, best/worst months |
| **Balance Health** | Average daily balance, lowest balance, ending balance, trend |
| **NSF/Overdraft** | Counts across 30/60/90-day windows, frequency patterns |
| **Debt Burden** | Active MCA positions, stacking burden, DSCR |
| **Risk Flags** | Lien detection, unusual transfers, anomaly detection |
| **Decision** | `needs_human_review: bool` — flags low-confidence extractions for manual review |

---

## Project Structure

```
app/
├── routes/              # 7 FastAPI routers (parse, classify, enrich, review, templates...)
├── extraction/          # 4-tier cascading PDF extraction orchestrator
├── classification/      # Document type identification (keyword + structural + LLM)
├── parsers/
│   ├── bank/            # 14 bank-specific templates + generic fallback + registry
│   └── tax/             # Business (1120, 1120S, 1065) and personal (1040, Sch C)
├── ai/                  # Gemini integration, enrichment engine, rate limiter
├── quality/             # Pre-flight document quality gate (blur, skew, contrast)
├── models/              # Pydantic v2 request/response schemas
├── utils/               # Currency parsing, date extraction, confidence computation
└── validation/          # Human review queue logic

frontend/
├── src/
│   ├── pages/           # ParsePage, ReviewPage, TemplatesPage
│   ├── components/      # DropZone, ResultsPanel (tabbed), ConfigPanel, Sidebar
│   ├── api/             # Axios client + TypeScript interfaces
│   └── hooks/           # Health check polling

tests/                   # pytest suite with synthetic PDF fixtures (reportlab)
infra/                   # Terraform — Lambda, API Gateway, ECR, CloudWatch, IAM
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- [Poppler](https://poppler.freedesktop.org/) — `brew install poppler` on macOS
- [Tesseract](https://github.com/tesseract-ocr/tesseract) — optional, enables OCR tier

### Setup

```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd frontend && npm install && cd ..

# Environment
cp .env.example .env
# Add your API keys:
#   GOOGLE_AI_API_KEY=your-gemini-key
#   LLAMA_CLOUD_API_KEY=your-llamaparse-key  (optional)
```

### Run

```bash
make dev              # Backend → http://localhost:8100
make frontend-dev     # Frontend → http://localhost:5173
make up               # Both via Docker Compose
make test             # pytest suite
```

### Docker

```bash
make build-local
docker run -p 8100:8100 --env-file .env yieldstream-qualify-local
```

---

## Deploy to AWS

Infrastructure is fully managed with Terraform:

```bash
cd infra
terraform init
terraform apply \
  -var="google_ai_api_key=$GOOGLE_AI_API_KEY" \
  -var="llama_cloud_api_key=$LLAMA_CLOUD_API_KEY"
```

Build, push, and deploy:

```bash
make build
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin <ECR_URL>
docker tag yieldstream-qualify:latest <ECR_URL>:latest
docker push <ECR_URL>:latest

aws lambda update-function-code \
  --function-name yieldstream-qualify \
  --image-uri <ECR_URL>:latest
```

---

## Design Decisions

### Cascading Extraction Tiers
PDFs are unpredictable — a bank-generated statement, a scanned fax, and a phone photo all need to work. The tiered architecture tries the fastest/cheapest method first (pdfplumber, ~200ms) and only escalates when quality thresholds aren't met. Each tier is independently timed and logged for observability.

### Template Registry Pattern
Each bank has idiosyncratic statement formats. Rather than one fragile generic parser, each bank gets a dedicated template subclass with its own regex patterns and field extraction logic. The registry scores every template against the document in parallel, picks the highest-confidence match, and maintains a thread-safe 30-day match history for monitoring template drift.

### Regex-First, LLM-Second
Structured financial documents have predictable formats. Regex extraction is fast, free, and deterministic. Gemini only kicks in when regex confidence drops below 0.5 — keeping per-request costs near zero for well-formed documents while still handling edge cases gracefully.

### Quality Gate Before Extraction
Rejecting a blurry photo early saves 5-10 seconds of extraction time and prevents returning garbage data with false confidence. The gate checks blur, skew, contrast, resolution, and corner cropping using PIL + NumPy.

### Confidence Scoring Throughout
Every pipeline stage reports a confidence score (0-1). The final response aggregates text quality, table extraction, and template match confidence into an overall score. Documents below 0.85 are automatically flagged with `needs_human_review: true`.

---

## License

Proprietary. All rights reserved.
