export const nav = {
  links: [
    { label: "Product", href: "#features" },
    { label: "Docs", href: "/docs" },
    { label: "Pricing", href: "#pricing" },
    { label: "Changelog", href: "/changelog" },
    { label: "Blog", href: "/blog" },
  ],
};

export const hero = {
  eyebrow: "DOCUMENT INTELLIGENCE API",
  headline: "Structured financial data from any bank statement.",
  subheadline:
    "Bank statements in. Decision-ready data out. Production-grade extraction with balance reconciliation, 25+ risk indicators, and multiple templates — built for fintechs that underwrite at scale.",
  primaryCTA: { label: "Create account", href: "/signup" },
  secondaryCTA: { label: "Read the docs", href: "/docs" },
  curlExample:
    'curl -X POST api.ledger.yieldstream.io/v1/parse \\\n  -H "Authorization: Bearer $LEDGER_API_KEY" \\\n  -F file=@statement.pdf',
};

export const trustBar = {
  metrics: [
    { value: "99.2%", label: "Extraction accuracy" },
    { value: "<12s", label: "Avg parse time" },
    { value: "14", label: "Bank templates" },
  ],
};

export const features = [
  {
    icon: "Layers",
    title: "Multi-tier parsing pipeline",
    description:
      "Template registry matches Chase, Bank of America, Wells Fargo, and 11 more. Falls back to generic LLM extraction with full traceability.",
  },
  {
    icon: "Scale",
    title: "Balance reconciliation",
    description:
      "Every parse cross-checks: starting balance + credits \u2212 debits = ending balance. Discrepancies flagged automatically.",
  },
  {
    icon: "Target",
    title: "Field-level confidence",
    description:
      "Every extracted field returns a confidence score. Set thresholds, route low-confidence parses to human review.",
  },
  {
    icon: "ShieldAlert",
    title: "Risk enrichment",
    description:
      "25+ indicators including NSF events, MCA stacking, daily debit patterns, revenue smoothing, and average daily balance trends.",
  },
  {
    icon: "EyeOff",
    title: "PII redaction",
    description:
      "Privacy Shield mode redacts names, addresses, account numbers while preserving financial structure.",
  },
  {
    icon: "FileStack",
    title: "Multi-file stitching",
    description:
      "Upload three monthly statements, get one unified 90-day view with deduplication and gap detection.",
  },
];

export const howItWorks = {
  eyebrow: "DEVELOPER EXPERIENCE",
  headline: "One API call. Structured ledger data.",
  tabs: [
    {
      label: "cURL",
      language: "bash",
      code: `curl -X POST https://api.ledger.yieldstream.io/parse \\
  -H "Authorization: Bearer $LEDGER_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "file_url": "https://files.example.com/chase_march_2024.pdf",
    "file_name": "chase_march_2024.pdf",
    "cross_check_balances": true,
    "include_enrichment": true
  }'`,
    },
    {
      label: "Python",
      language: "python",
      code: `import requests

resp = requests.post(
    "https://api.ledger.yieldstream.io/parse",
    headers={"Authorization": f"Bearer {LEDGER_API_KEY}"},
    json={
        "file_url": "https://files.example.com/chase_march_2024.pdf",
        "file_name": "chase_march_2024.pdf",
        "cross_check_balances": True,
        "include_enrichment": True,
    },
)

result = resp.json()
print(result["cash_flow"]["ending_balance"])   # 14892.37
print(result["validation"]["balance_check"])   # "passed"
print(result["confidence"]["overall"])         # 0.994`,
    },
    {
      label: "Node",
      language: "javascript",
      code: `const resp = await fetch('https://api.ledger.yieldstream.io/parse', {
  method: 'POST',
  headers: {
    Authorization: \`Bearer \${process.env.LEDGER_API_KEY}\`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    file_url: 'https://files.example.com/chase_march_2024.pdf',
    file_name: 'chase_march_2024.pdf',
    cross_check_balances: true,
    include_enrichment: true,
  }),
});

const result = await resp.json();
console.log(result.cash_flow.ending_balance);  // 14892.37
console.log(result.validation.balance_check);  // "passed"
console.log(result.confidence.overall);        // 0.994`,
    },
    {
      label: "Go",
      language: "go",
      code: `package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

func main() {
    body, _ := json.Marshal(map[string]any{
        "file_url":             "https://files.example.com/chase_march_2024.pdf",
        "file_name":            "chase_march_2024.pdf",
        "cross_check_balances": true,
        "include_enrichment":   true,
    })

    req, _ := http.NewRequest("POST",
        "https://api.ledger.yieldstream.io/parse",
        bytes.NewReader(body))
    req.Header.Set("Authorization", "Bearer "+apiKey)
    req.Header.Set("Content-Type", "application/json")

    resp, _ := http.DefaultClient.Do(req)
    defer resp.Body.Close()
}`,
    },
  ],
  responsePreview: `{
  "status": "succeeded",
  "document": {
    "type": "bank_statement",
    "subtype": "checking",
    "page_count": 6,
    "extraction_method": "pdfplumber",
    "template_used": "chase_checking_v3"
  },
  "period": { "start": "2024-03-01", "end": "2024-03-31" },
  "identity": {
    "account_holder_name": "ACME LOGISTICS LLC",
    "account_number_last4": "4821",
    "business_name": "ACME LOGISTICS LLC",
    "consistency_check": "passed"
  },
  "cash_flow": {
    "starting_balance": 12450.82,
    "ending_balance": 14892.37,
    "total_inflows": 8920.00,
    "total_outflows": 6478.45,
    "net_change": 2441.55,
    "average_daily_balance": 13420.15,
    "min_balance": 9134.20,
    "ending_balance_trend": "growing",
    "nsf_count": 0,
    "negative_balance_days": 0
  },
  "validation": {
    "balance_check": "passed",
    "expected_ending": 14892.37,
    "actual_ending": 14892.37,
    "discrepancy": 0.00
  },
  "confidence": {
    "overall": 0.994,
    "needs_human_review": false
  }
}`,
  responseFull: `{
  "status": "succeeded",
  "error": null,
  "document": {
    "type": "bank_statement",
    "subtype": "checking",
    "page_count": 6,
    "extraction_method": "pdfplumber",
    "template_used": "chase_checking_v3"
  },
  "identity": {
    "account_holder_name": "ACME LOGISTICS LLC",
    "account_number_last4": "4821",
    "business_name": "ACME LOGISTICS LLC",
    "address": "1420 W INDUSTRIAL BLVD, DALLAS TX 75207",
    "ein": "47-2918334",
    "consistency_check": "passed"
  },
  "period": { "start": "2024-03-01", "end": "2024-03-31" },
  "cash_flow": {
    "starting_balance": 12450.82,
    "ending_balance": 14892.37,
    "total_inflows": 8920.00,
    "total_outflows": 6478.45,
    "net_change": 2441.55,
    "min_balance": 9134.20,
    "min_balance_date": "2024-03-18",
    "average_daily_balance": 13420.15,
    "ending_balance_trend": "growing",
    "days_below_threshold": 0,
    "negative_balance_days": 0,
    "nsf_count": 0,
    "nsf_count_30d": 0,
    "nsf_count_60d": 0,
    "nsf_count_90d": 1,
    "overdraft_events": [],
    "suspicious_transfers": [],
    "anomalies": []
  },
  "revenue": {
    "gross_deposits": 8920.00,
    "deposit_count": 47,
    "monthly_average": 8740.50,
    "trend": "growing",
    "volatility": 0.18,
    "best_month": 9420.10,
    "worst_month": 7890.40,
    "avg_transaction_size": 189.79,
    "processor_deposits": [
      { "processor": "Stripe",  "total": 4210.55, "transaction_count": 22 },
      { "processor": "Square",  "total": 2890.20, "transaction_count": 18 }
    ],
    "non_processor_inflows": 1819.25,
    "recurring_revenue_estimate": 6200.00,
    "chargebacks": { "count": 1, "total": 89.00, "percent_of_revenue": 0.01 },
    "concentration": { "top_counterparty_percent": 0.31, "top_5_percent": 0.62 },
    "seasonality_signal": "stable",
    "anomalies": []
  },
  "debt": {
    "active_positions": [
      {
        "type": "term_loan",
        "lender_name": "Bluevine",
        "daily_debit": null,
        "monthly_payment": 482.10,
        "estimated_balance": 14200.00,
        "first_seen": "2023-11-04"
      }
    ],
    "total_daily_debt_service": 0.00,
    "total_monthly_debt_service": 482.10,
    "stacking_burden_pct": 0.054,
    "dscr": 5.06,
    "lien_flags": [],
    "anomalies": []
  },
  "expenses": {
    "payroll":               { "monthly_total": 3120.00, "counterparty": "Gusto",     "provider": "Gusto",   "frequency": "biweekly" },
    "rent":                  { "monthly_total": 1850.00, "counterparty": "RIVERSIDE PROP MGMT", "provider": null, "frequency": "monthly" },
    "utilities":             { "monthly_total": 312.45,  "counterparty": "ONCOR",     "provider": null,      "frequency": "monthly" },
    "insurance":             { "monthly_total": 218.00,  "counterparty": "NEXT INS",  "provider": "Next Insurance", "frequency": "monthly" },
    "software_subscriptions":{ "monthly_total": 184.20,  "counterparty": null,        "provider": null,      "frequency": "monthly" },
    "tax_payments":          { "federal": 0.00, "state": 0.00, "last_seen": "2024-01-15" }
  },
  "validation": {
    "balance_check": "passed",
    "expected_ending": 14892.37,
    "actual_ending": 14892.37,
    "discrepancy": 0.00
  },
  "summary": {
    "narrative": "Healthy operating account with growing balance, strong DSCR, and no NSF activity in the trailing 60 days.",
    "key_concerns": ["One NSF event 90+ days prior"],
    "strengths": ["DSCR > 5.0", "No stacking", "Recurring revenue ~70% of deposits"]
  },
  "confidence": {
    "overall": 0.994,
    "text_quality": 0.998,
    "table_extraction": 0.991,
    "template_match": 0.997,
    "by_category": {
      "cash_flow": 0.998,
      "revenue":   0.992,
      "debt":      0.985,
      "expenses":  0.989,
      "identity":  0.999
    },
    "needs_human_review": false
  },
  "extraction_method": "pdfplumber",
  "page_count": 6,
  "processing_time_ms": 3247,
  "template_match": {
    "id": "chase_checking_v3",
    "bank_name": "JPMorgan Chase",
    "confidence": 0.997,
    "fallback_used": false,
    "signals": [
      { "category": "header_logo",  "description": "Chase logo detected on page 1" },
      { "category": "layout_match", "description": "Account summary block matches v3 layout" }
    ],
    "alternatives": [
      { "id": "chase_checking_v2", "bank_name": "JPMorgan Chase", "confidence": 0.612 }
    ]
  },
  "metadata": {
    "winning_tier": "pdfplumber",
    "tiers_attempted": 1,
    "total_processing_time_ms": 3247,
    "bank_detected": "JPMorgan Chase",
    "template_used": "chase_checking_v3",
    "template_match_confidence": 0.997,
    "document_type_classified": "bank_statement",
    "classification_confidence": 0.998,
    "classification_method": "structural",
    "fields_extracted_count": 13,
    "fields_missing": [],
    "needs_human_review": false,
    "gemini_tokens_used": null,
    "gemini_cost_estimate": null
  },
  "quality": {
    "passed": true,
    "overall_score": 0.97,
    "processing_allowed": true,
    "issues": [],
    "rejection_reason": null,
    "recommendation": null
  },
  "parsed_data": null
}`,
  callouts: [
    { field: "template_match", label: "Template matched" },
    { field: "validation.balance_check", label: "Balance check passed" },
    { field: "confidence.by_category", label: "Per-category confidence" },
    { field: "cash_flow / debt", label: "Underwriter signals computed" },
  ],
};

export const templateCoverage = {
  eyebrow: "BANK TEMPLATES",
  headline: "14 templates. 99%+ accuracy on supported banks.",
  banks: [
    { name: "Chase", accuracy: "99.4%" },
    { name: "Bank of America", accuracy: "99.1%" },
    { name: "Wells Fargo", accuracy: "98.7%" },
    { name: "Citi", accuracy: "99.0%" },
    { name: "US Bank", accuracy: "98.9%" },
    { name: "PNC", accuracy: "98.5%" },
    { name: "Capital One", accuracy: "99.2%" },
    { name: "TD Bank", accuracy: "98.8%" },
    { name: "Truist", accuracy: "98.3%" },
    { name: "Fifth Third", accuracy: "98.1%" },
    { name: "Regions", accuracy: "97.9%" },
    { name: "KeyBank", accuracy: "98.0%" },
    { name: "Huntington", accuracy: "97.8%" },
    { name: "M&T Bank", accuracy: "98.2%" },
  ],
  fallbackNote:
    "Don't see your bank? The generic parser handles 4,200+ institutions.",
  fallbackCTA: { label: "Request a template", href: "/docs/templates" },
};

export const metrics = {
  eyebrow: "TRUST LAYER",
  headline: "Auditable by design.",
  items: [
    { value: "99.2%", label: "Field extraction accuracy" },
    { value: "100%", label: "Balance reconciliation coverage" },
    { value: "<12s", label: "Median parse time (10 pages)" },
    { value: "25+", label: "Risk indicators per document" },
  ],
  description:
    "Every parse result includes a full validation trace: which template matched, how confidence was computed, and where each field was sourced from. No black-box outputs. Built for teams that answer to auditors.",
};

export const comparison = {
  eyebrow: "WHY LEDGER",
  headline: "Built for finance, not generic OCR.",
  headers: ["Feature", "Ledger", "Generic OCR", "LLM-only"],
  rows: [
    {
      feature: "Bank-specific templates",
      ledger: true,
      ocr: false,
      llm: false,
    },
    {
      feature: "Balance reconciliation",
      ledger: true,
      ocr: false,
      llm: "partial",
    },
    {
      feature: "Field-level confidence",
      ledger: true,
      ocr: "partial",
      llm: false,
    },
    { feature: "PII redaction", ledger: true, ocr: false, llm: false },
    { feature: "Risk enrichment", ledger: true, ocr: false, llm: false },
    { feature: "Multi-file stitching", ledger: true, ocr: false, llm: false },
    { feature: "Audit trail", ledger: true, ocr: "partial", llm: false },
  ],
};

export const useCases = {
  eyebrow: "WHO USES LEDGER",
  headline: "Built for the institutional middle office.",
  items: [
    {
      icon: "BadgeDollarSign",
      title: "MCA underwriters",
      description:
        "Automated lender matching, NSF detection, average daily balance calculation, and revenue consistency scoring. Process applications in minutes, not hours.",
    },
    {
      icon: "Building2",
      title: "Lenders and banks",
      description:
        "KYB document intake, statement verification, and fraud screening. Validate income claims against extracted transaction data with field-level confidence.",
    },
    {
      icon: "Calculator",
      title: "Accounting platforms",
      description:
        "Bank statement reconciliation at scale. Stitch multi-month statements, extract transaction categories, and flag discrepancies automatically.",
    },
  ],
};

export const pricing = {
  eyebrow: "PRICING",
  headline: "Pay per document. No platform fees.",
  subheadline:
    "All plans include balance validation, confidence scoring, and PII redaction.",
  tiers: [
    {
      name: "Developer",
      price: "Free",
      priceDetail: "100 parses/month",
      features: [
        "100 parses per month",
        "Community support",
        "Basic templates (top 5 banks)",
        "Balance validation",
        "Confidence scoring",
      ],
      cta: { label: "Create account", href: "/signup" },
      highlighted: false,
    },
    {
      name: "Production",
      price: "$0.10",
      priceDetail: "per parse",
      features: [
        "Volume discounts available",
        "All 14 bank templates",
        "Full validation + enrichment",
        "PII redaction",
        "Email support",
        "Multi-file stitching",
      ],
      cta: { label: "Create account", href: "/signup" },
      highlighted: true,
    },
    {
      name: "Institutional",
      price: "Custom",
      priceDetail: "annual contract",
      features: [
        "Guaranteed SLA",
        "Dedicated infrastructure",
        "Custom template development",
        "Direct integration support",
        "SOC 2 compliance docs",
        "Priority enrichment updates",
      ],
      cta: { label: "Talk to sales", href: "/contact" },
      highlighted: false,
    },
  ],
};

export const finalCTA = {
  headline: "Start parsing in five minutes.",
  subheadline: "Free to try. No credit card. 100 parses on the house.",
  primaryCTA: { label: "Create account", href: "/signup" },
  secondaryCTA: { label: "Read the docs", href: "/docs" },
  installLine: "npm install @yieldstream/ledger",
};

export const footer = {
  sections: [
    {
      title: "Product",
      links: [
        { label: "Features", href: "#features" },
        { label: "Pricing", href: "#pricing" },
        { label: "Templates", href: "#templates" },
        { label: "Changelog", href: "/changelog" },
        { label: "Status", href: "/status" },
      ],
    },
    {
      title: "Developers",
      links: [
        { label: "Documentation", href: "/docs" },
        { label: "API reference", href: "/docs/api" },
        { label: "SDKs", href: "/docs/sdks" },
        { label: "Examples", href: "/docs/examples" },
        { label: "Postman collection", href: "/docs/postman" },
      ],
    },
    {
      title: "Company",
      links: [
        { label: "About", href: "/about" },
        { label: "Blog", href: "/blog" },
        { label: "YieldStream platform", href: "https://yieldstream.io" },
        { label: "Contact", href: "/contact" },
      ],
    },
    {
      title: "Legal",
      links: [
        { label: "Terms", href: "/terms" },
        { label: "Privacy", href: "/privacy" },
        { label: "Security", href: "/security" },
        { label: "DPA", href: "/dpa" },
      ],
    },
  ],
  copyright:
    "\u00A9 2026 YieldStream LLC. Ledger is a product of YieldStream LLC.",
};
