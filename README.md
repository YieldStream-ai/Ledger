# YieldStream Qualify

**Document parsing and financial intelligence API for merchant cash advance underwriting.**

YieldStream Qualify extracts structured financial data from bank statements, tax returns, MCA applications, and approval letters — then enriches it with 25+ computed risk indicators to power automated underwriting decisions.

---

## Why This Exists

MCA underwriters manually review hundreds of bank statements and tax documents per week. Each review takes 15-30 minutes of scanning PDFs, pulling numbers into spreadsheets, and calculating metrics like average daily balance, NSF frequency, and existing MCA burden.

This API reduces that to a single POST request. Upload a document, get back structured data with confidence scores and risk flags — ready for decisioning.

---

## Architecture

```
                         ┌─────────────────────────┐
                         │      API Gateway         │
                         │   (rate: 5 req/s)        │
                         └────────┬────────────────-┘
                                  │
                         ┌────────▼────────────────-┐
                         │    AWS Lambda (FastAPI)   │
                         │    512 MB  /  60s timeout │
                         └────────┬────────────────-┘
                                  │
            ┌─────────────────────┼──────────────────────┐
            ▼                     ▼                      ▼
     ┌──────────────┐    ┌───────────────┐     ┌─────────────────┐
     │ Quality Gate  │    │ Extraction    │     │ Classification  │
     │               │    │ Orchestrator  │     │                 │
     │ blur, skew,   │    │               │     │ keyword match   │
     │ contrast,     │    │ Tier 1: pdfplumber  │ structural      │
     │ photo detect  │    │ Tier 2: PyMuPDF     │ Gemini fallback │
     └──────────────┘    │ Tier 3: Tesseract   └─────────────────┘
                         │ Tier 4: LlamaParse │
                         └───────┬────────────┘
                                 │
               ┌─────────────────┼─────────────────┐
               ▼                 ▼                  ▼
      ┌────────────────┐ ┌──────────────┐  ┌───────────────┐
      │ Bank Statement │ │  Tax Return  │  │ MCA Approval  │
      │ Parser         │ │  Parser      │  │ Letter Parser │
      │                │ │              │  │               │
      │ 14 bank        │ │ 1120, 1120S, │  │ regex + LLM   │
      │ templates +    │ │ 1065, Sch C, │  │ merge logic   │
      │ generic        │ │ 1040         │  │               │
      └────────┬───────┘ └──────────────┘  └───────────────┘
               │
      ┌────────▼───────┐
      │  Enrichment    │
      │  Engine        │
      │                │
      │  25+ risk      │
      │  indicators    │
      │  via Gemini    │
      └────────────────┘
```

### Processing Pipeline

1. **Quality Gate** — Pre-flight image analysis rejects blurry, skewed, or poorly-lit documents before wasting compute on extraction
2. **Extraction Orchestrator** — Cascading tiers attempt text extraction with automatic fallback. Each tier is timed and logged
3. **Classification** — Identifies document type via keyword matching with structural pattern confirmation. Falls back to Gemini when confidence is below 0.5
4. **Type-Specific Parsing** — Routes to the appropriate parser. Bank statements use a template registry that matches against 14 major US banks
5. **Enrichment** — Optional Gemini-powered financial analysis computing revenue trends, DSCR, MCA stacking burden, and anomaly detection

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Runtime** | Python 3.12, FastAPI, Pydantic v2 |
| **PDF Extraction** | pdfplumber, PyMuPDF, Tesseract OCR, LlamaParse |
| **AI/ML** | Google Gemini 2.0 Flash Lite |
| **Infrastructure** | AWS Lambda, API Gateway v2, ECR, CloudWatch |
| **IaC** | Terraform |
| **Testing** | pytest, pytest-asyncio, reportlab (synthetic PDFs) |
| **Containerization** | Docker (Lambda + local dev images) |

---

## API

### Parse a Document

```bash
curl -X POST https://your-api.com/parse \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://example.com/statement.pdf",
    "include_enrichment": true,
    "business_name": "Acme Corp",
    "industry": "retail"
  }'
```

**Response** includes:
- Extracted text and tables
- Document classification with confidence score
- Structured parsed data (transactions, summaries, tax fields)
- Extraction tier logs (which method worked, timing)
- Quality assessment results
- Financial enrichment (if requested)

### All Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Extractor availability check |
| `POST` | `/parse` | Parse document from URL |
| `POST` | `/parse/upload` | Parse uploaded file (multipart) |
| `POST` | `/classify` | Classify document type only |
| `POST` | `/extract-approval` | Extract MCA approval letter terms (upload) |
| `POST` | `/extract-approval/url` | Extract MCA approval letter terms (URL) |
| `POST` | `/v1/enrich` | Standalone financial enrichment |

---

## Supported Document Types

### Bank Statements (14 templates)

Chase, Bank of America, Wells Fargo, PNC, US Bank, Capital One, Regions, Truist, Citizens, Fifth Third, BMO Harris, Navy Federal Credit Union — plus a generic fallback for unrecognized banks.

Each template extracts:
- Account summary (opening/closing balance, deposits, withdrawals)
- Individual transactions with date, description, and amount
- Derived metrics: average daily balance, negative balance days, largest transactions, revenue breakdown
- NSF/overdraft detection
- MCA payment identification

### Tax Returns

| Form | Type |
|---|---|
| 1120 | C-Corporation |
| 1120S | S-Corporation |
| 1065 | Partnership |
| Schedule C | Sole Proprietorship |
| 1040 | Personal |

Extracts gross receipts, net income, officer compensation, and filing period.

### MCA Documents

- **Applications** — Business details, funding amount, owner information, existing debt positions
- **Approval Letters** — Offer terms, factor rates, payment schedules, stipulations, expiration dates

---

## Enrichment: Financial Intelligence

When `include_enrichment` is set, the API returns 25+ computed indicators:

**Revenue Analysis**
- Monthly average revenue, trend direction, volatility percentage, best/worst months

**Balance Health**
- Average daily balance, lowest balance, ending balance, trend

**Risk Indicators**
- NSF counts (30/60/90 day windows)
- Negative balance days
- Balance threshold breaches
- Active MCA positions and stacking burden
- Debt service coverage ratio (DSCR)
- Lien detection, unusual transfers, anomalies

**Output Flags**
- `needs_human_review: bool` — triggers manual underwriting when confidence is low

---

## Project Structure

```
app/
├── routes/            # FastAPI endpoints
├── extraction/        # Multi-tier PDF text extraction
├── classification/    # Document type identification
├── parsers/
│   ├── bank/          # 14 bank templates + generic fallback
│   └── tax/           # Business and personal tax parsers
├── ai/                # Gemini integration, enrichment engine
├── quality/           # Pre-flight document quality gate
├── models/            # Pydantic request/response schemas
└── utils/             # Currency, date, and confidence helpers

tests/                 # Unit + integration tests with synthetic fixtures
infra/                 # Terraform (Lambda, API Gateway, ECR, IAM)
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- [Poppler](https://poppler.freedesktop.org/) (`brew install poppler` on macOS)
- [Tesseract](https://github.com/tesseract-ocr/tesseract) (optional, for OCR tier)

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Create a `.env` file:

```
GOOGLE_AI_API_KEY=your-gemini-key
LLAMA_CLOUD_API_KEY=your-llamaparse-key    # optional
```

### Run Locally

```bash
make dev    # starts on http://localhost:8100
```

### Run Tests

```bash
make test
```

### Docker (Local)

```bash
make build-local
docker run -p 8100:8100 --env-file .env yieldstream-qualify-local
```

---

## Deploy to AWS

Infrastructure is managed with Terraform in `infra/`.

```bash
cd infra
terraform init
terraform apply \
  -var="google_ai_api_key=$GOOGLE_AI_API_KEY" \
  -var="llama_cloud_api_key=$LLAMA_CLOUD_API_KEY"
```

Then build and push the container:

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

**Cascading extraction tiers** — PDFs are unpredictable. A bank-generated statement, a scanned fax, and a phone photo of a document all need to work. The tiered approach tries the fastest/cheapest method first and escalates only when quality thresholds aren't met.

**Template registry pattern** — Each bank has idiosyncratic statement formats. Rather than one fragile generic parser, each bank gets its own template with specific regex patterns. The registry scores each template against the document and picks the best match. A generic fallback catches everything else.

**Regex-first, LLM-second** — Structured financial documents have predictable formats. Regex extraction is fast, free, and deterministic. Gemini only kicks in when regex confidence is low, keeping costs down and latency predictable.

**Quality gate before extraction** — Rejecting a blurry phone photo early saves 5-10 seconds of extraction time and avoids returning garbage data with false confidence.

**Confidence scoring throughout** — Every stage reports confidence. The final response makes it clear whether the data is reliable or needs human review.

---

## License

Proprietary. All rights reserved.
