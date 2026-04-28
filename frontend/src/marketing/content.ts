export const nav = {
  links: [
    { label: 'Product', href: '#features' },
    { label: 'Docs', href: '/docs' },
    { label: 'Pricing', href: '#pricing' },
    { label: 'Changelog', href: '/changelog' },
    { label: 'Blog', href: '/blog' },
  ],
}

export const hero = {
  eyebrow: 'DOCUMENT INTELLIGENCE API',
  headline: 'Structured financial data from any bank statement.',
  subheadline:
    'Production-grade extraction for bank statements, tax returns, and merchant cash advance underwriting. 14 bank templates, balance reconciliation, and 25+ risk indicators in a single API call.',
  primaryCTA: { label: 'Create account', href: '/signup' },
  secondaryCTA: { label: 'Read the docs', href: '/docs' },
  curlExample:
    'curl -X POST api.ledger.yieldstream.io/v1/parse \\\n  -H "Authorization: Bearer $LEDGER_API_KEY" \\\n  -F file=@statement.pdf',
}

export const trustBar = {
  metrics: [
    { value: '99.2%', label: 'Extraction accuracy' },
    { value: '<12s', label: 'Avg parse time' },
    { value: '14', label: 'Bank templates' },
  ],
}

export const features = [
  {
    icon: 'Layers',
    title: 'Multi-tier parsing pipeline',
    description:
      'Template registry matches Chase, Bank of America, Wells Fargo, and 11 more. Falls back to generic LLM extraction with full traceability.',
  },
  {
    icon: 'Scale',
    title: 'Balance reconciliation',
    description:
      'Every parse cross-checks: starting balance + credits \u2212 debits = ending balance. Discrepancies flagged automatically.',
  },
  {
    icon: 'Target',
    title: 'Field-level confidence',
    description:
      'Every extracted field returns a confidence score. Set thresholds, route low-confidence parses to human review.',
  },
  {
    icon: 'ShieldAlert',
    title: 'Risk enrichment',
    description:
      '25+ indicators including NSF events, MCA stacking, daily debit patterns, revenue smoothing, and average daily balance trends.',
  },
  {
    icon: 'EyeOff',
    title: 'PII redaction',
    description:
      'Privacy Shield mode redacts names, addresses, account numbers while preserving financial structure.',
  },
  {
    icon: 'FileStack',
    title: 'Multi-file stitching',
    description:
      'Upload three monthly statements, get one unified 90-day view with deduplication and gap detection.',
  },
]

export const howItWorks = {
  eyebrow: 'DEVELOPER EXPERIENCE',
  headline: 'One API call. Structured ledger data.',
  tabs: [
    {
      label: 'cURL',
      language: 'bash',
      code: `curl -X POST https://api.ledger.yieldstream.io/v1/parse \\
  -H "Authorization: Bearer $LEDGER_API_KEY" \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@chase_march_2024.pdf" \\
  -F "config[validate]=true" \\
  -F "config[enrich]=true"`,
    },
    {
      label: 'Python',
      language: 'python',
      code: `import ledger

client = ledger.Client(api_key="sk_live_...")

result = client.parse(
    file=open("chase_march_2024.pdf", "rb"),
    config={"validate": True, "enrich": True}
)

print(result.summary.ending_balance)  # 14_892.37
print(result.validation.status)       # "passed"
print(result.confidence.overall)      # 0.994`,
    },
    {
      label: 'Node',
      language: 'javascript',
      code: `import Ledger from '@yieldstream/ledger';

const client = new Ledger({ apiKey: 'sk_live_...' });

const result = await client.parse({
  file: fs.createReadStream('chase_march_2024.pdf'),
  config: { validate: true, enrich: true }
});

console.log(result.summary.endingBalance);  // 14892.37
console.log(result.validation.status);      // "passed"
console.log(result.confidence.overall);     // 0.994`,
    },
    {
      label: 'Go',
      language: 'go',
      code: `package main

import "github.com/yieldstream/ledger-go"

func main() {
    client := ledger.NewClient("sk_live_...")

    result, err := client.Parse(ledger.ParseRequest{
        File:   "chase_march_2024.pdf",
        Config: ledger.Config{Validate: true, Enrich: true},
    })

    fmt.Println(result.Summary.EndingBalance) // 14892.37
    fmt.Println(result.Validation.Status)     // "passed"
    fmt.Println(result.Confidence.Overall)    // 0.994
}`,
    },
  ],
  response: `{
  "id": "parse_8f3a2b1c",
  "status": "completed",
  "template": {
    "matched": "chase_checking_v3",
    "confidence": 0.997
  },
  "summary": {
    "institution": "JPMorgan Chase",
    "account_type": "checking",
    "period": "2024-03-01/2024-03-31",
    "starting_balance": 12450.82,
    "ending_balance": 14892.37,
    "total_credits": 8920.00,
    "total_debits": 6478.45
  },
  "validation": {
    "status": "passed",
    "balance_check": "12450.82 + 8920.00 - 6478.45 = 14892.37"
  },
  "confidence": {
    "overall": 0.994,
    "fields": {
      "starting_balance": 0.999,
      "ending_balance": 0.998,
      "transactions": 0.991
    }
  },
  "risk_indicators": {
    "nsf_events": 0,
    "mca_payments_detected": false,
    "avg_daily_balance": 13420.15,
    "revenue_consistency": 0.87
  }
}`,
  callouts: [
    { field: 'template.matched', label: 'Template matched' },
    { field: 'validation.status', label: 'Validation passed' },
    { field: 'confidence.fields', label: 'Per-field confidence' },
    { field: 'risk_indicators', label: 'Risk indicators auto-computed' },
  ],
}

export const templateCoverage = {
  eyebrow: 'BANK TEMPLATES',
  headline: '14 templates. 99%+ accuracy on supported banks.',
  banks: [
    { name: 'Chase', accuracy: '99.4%' },
    { name: 'Bank of America', accuracy: '99.1%' },
    { name: 'Wells Fargo', accuracy: '98.7%' },
    { name: 'Citi', accuracy: '99.0%' },
    { name: 'US Bank', accuracy: '98.9%' },
    { name: 'PNC', accuracy: '98.5%' },
    { name: 'Capital One', accuracy: '99.2%' },
    { name: 'TD Bank', accuracy: '98.8%' },
    { name: 'Truist', accuracy: '98.3%' },
    { name: 'Fifth Third', accuracy: '98.1%' },
    { name: 'Regions', accuracy: '97.9%' },
    { name: 'KeyBank', accuracy: '98.0%' },
    { name: 'Huntington', accuracy: '97.8%' },
    { name: 'M&T Bank', accuracy: '98.2%' },
  ],
  fallbackNote:
    "Don't see your bank? The generic parser handles 4,200+ institutions.",
  fallbackCTA: { label: 'Request a template', href: '/docs/templates' },
}

export const metrics = {
  eyebrow: 'TRUST LAYER',
  headline: 'Auditable by design.',
  items: [
    { value: '99.2%', label: 'Field extraction accuracy' },
    { value: '100%', label: 'Balance reconciliation coverage' },
    { value: '<12s', label: 'Median parse time (10 pages)' },
    { value: '25+', label: 'Risk indicators per document' },
  ],
  description:
    'Every parse result includes a full validation trace: which template matched, how confidence was computed, and where each field was sourced from. No black-box outputs. Built for teams that answer to auditors.',
}

export const comparison = {
  eyebrow: 'WHY LEDGER',
  headline: 'Built for finance, not generic OCR.',
  headers: ['Feature', 'Ledger', 'Generic OCR', 'LLM-only'],
  rows: [
    { feature: 'Bank-specific templates', ledger: true, ocr: false, llm: false },
    { feature: 'Balance reconciliation', ledger: true, ocr: false, llm: 'partial' },
    { feature: 'Field-level confidence', ledger: true, ocr: 'partial', llm: false },
    { feature: 'PII redaction', ledger: true, ocr: false, llm: false },
    { feature: 'Risk enrichment', ledger: true, ocr: false, llm: false },
    { feature: 'Multi-file stitching', ledger: true, ocr: false, llm: false },
    { feature: 'Audit trail', ledger: true, ocr: 'partial', llm: false },
  ],
}

export const useCases = {
  eyebrow: 'WHO USES LEDGER',
  headline: 'Built for the institutional middle office.',
  items: [
    {
      icon: 'BadgeDollarSign',
      title: 'MCA underwriters',
      description:
        'Automated lender matching, NSF detection, average daily balance calculation, and revenue consistency scoring. Process applications in minutes, not hours.',
    },
    {
      icon: 'Building2',
      title: 'Lenders and banks',
      description:
        'KYB document intake, statement verification, and fraud screening. Validate income claims against extracted transaction data with field-level confidence.',
    },
    {
      icon: 'Calculator',
      title: 'Accounting platforms',
      description:
        'Bank statement reconciliation at scale. Stitch multi-month statements, extract transaction categories, and flag discrepancies automatically.',
    },
  ],
}

export const pricing = {
  eyebrow: 'PRICING',
  headline: 'Pay per document. No platform fees.',
  subheadline: 'All plans include balance validation, confidence scoring, and PII redaction.',
  tiers: [
    {
      name: 'Developer',
      price: 'Free',
      priceDetail: '100 parses/month',
      features: [
        '100 parses per month',
        'Community support',
        'Basic templates (top 5 banks)',
        'Balance validation',
        'Confidence scoring',
      ],
      cta: { label: 'Create account', href: '/signup' },
      highlighted: false,
    },
    {
      name: 'Production',
      price: '$0.10',
      priceDetail: 'per parse',
      features: [
        'Volume discounts available',
        'All 14 bank templates',
        'Full validation + enrichment',
        'PII redaction',
        'Email support',
        'Multi-file stitching',
      ],
      cta: { label: 'Create account', href: '/signup' },
      highlighted: true,
    },
    {
      name: 'Institutional',
      price: 'Custom',
      priceDetail: 'annual contract',
      features: [
        'Guaranteed SLA',
        'Dedicated infrastructure',
        'Custom template development',
        'Direct integration support',
        'SOC 2 compliance docs',
        'Priority enrichment updates',
      ],
      cta: { label: 'Talk to sales', href: '/contact' },
      highlighted: false,
    },
  ],
}

export const finalCTA = {
  headline: 'Start parsing in five minutes.',
  subheadline: 'Free to try. No credit card. 100 parses on the house.',
  primaryCTA: { label: 'Create account', href: '/signup' },
  secondaryCTA: { label: 'Read the docs', href: '/docs' },
  installLine: 'npm install @yieldstream/ledger',
}

export const footer = {
  sections: [
    {
      title: 'Product',
      links: [
        { label: 'Features', href: '#features' },
        { label: 'Pricing', href: '#pricing' },
        { label: 'Templates', href: '#templates' },
        { label: 'Changelog', href: '/changelog' },
        { label: 'Status', href: '/status' },
      ],
    },
    {
      title: 'Developers',
      links: [
        { label: 'Documentation', href: '/docs' },
        { label: 'API reference', href: '/docs/api' },
        { label: 'SDKs', href: '/docs/sdks' },
        { label: 'Examples', href: '/docs/examples' },
        { label: 'Postman collection', href: '/docs/postman' },
      ],
    },
    {
      title: 'Company',
      links: [
        { label: 'About', href: '/about' },
        { label: 'Blog', href: '/blog' },
        { label: 'YieldStream platform', href: 'https://yieldstream.io' },
        { label: 'Contact', href: '/contact' },
      ],
    },
    {
      title: 'Legal',
      links: [
        { label: 'Terms', href: '/terms' },
        { label: 'Privacy', href: '/privacy' },
        { label: 'Security', href: '/security' },
        { label: 'DPA', href: '/dpa' },
      ],
    },
  ],
  copyright: '\u00A9 2026 YieldStream LLC. Ledger is a product of YieldStream LLC.',
}
