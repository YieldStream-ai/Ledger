import { useState, useCallback, useMemo } from "react";
import { ChevronDown, ChevronRight, Play, Settings } from "lucide-react";
import type { ParseConfig } from "../../api/types";

interface ConfigPanelProps {
  config: ParseConfig;
  onChange: (config: ParseConfig) => void;
  onRunParse: () => void;
  isRunning: boolean;
  hasFiles: boolean;
  fileCount?: number;
}

const DOC_TYPES = [
  { value: "", label: "Auto-detect" },
  { value: "bank_statement", label: "Bank Statement" },
  { value: "business_tax_return", label: "Business Tax Return" },
  { value: "personal_tax_return", label: "Personal Tax Return" },
  { value: "mca_application", label: "MCA Application" },
];

const PAGE_RANGE_OPTIONS = [
  { value: "all", label: "All pages" },
  { value: "1", label: "First page only" },
  { value: "1-3", label: "Pages 1–3" },
  { value: "1-5", label: "Pages 1–5" },
  { value: "custom", label: "Custom range" },
];

const ANON_MODES = [
  { value: "none", label: "None" },
  { value: "redact", label: "Redact PII" },
  { value: "mask", label: "Mask (partial)" },
];

const STORAGE_KEY = "ys-config-sections";

type SectionKey = "document" | "validation" | "enrichment";

const DEFAULT_OPEN: Record<SectionKey, boolean> = {
  document: true,
  validation: true,
  enrichment: false,
};

function loadSectionState(): Record<SectionKey, boolean> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULT_OPEN, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return { ...DEFAULT_OPEN };
}

function saveSectionState(state: Record<SectionKey, boolean>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function SectionHeader({
  label,
  isOpen,
  onToggle,
}: {
  label: string;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const Chevron = isOpen ? ChevronDown : ChevronRight;
  return (
    <button
      type="button"
      onClick={onToggle}
      className="flex items-center gap-1.5 w-full pt-1 pb-4 text-left group"
    >
      <Chevron className="w-3.5 h-3.5 text-gray-400 group-hover:text-gray-600 transition-colors" />
      <span className="text-xs font-medium text-gray-500 uppercase tracking-[0.08em]">
        {label}
      </span>
    </button>
  );
}

function getPageLabel(pageRange: string): string {
  const opt = PAGE_RANGE_OPTIONS.find((o) => o.value === pageRange);
  return opt ? opt.label : pageRange;
}

function getDocTypeLabel(hint: string): string {
  if (!hint) return "Auto-detect document type";
  const dt = DOC_TYPES.find((d) => d.value === hint);
  return dt ? dt.label : hint;
}

function estimateCostAndTime(
  config: ParseConfig,
  fileCount: number
): { cost: string; time: string } {
  const baseCostPerFile = 0.02;
  const baseTimePerFile = 6;
  const enrichmentMultiplier = config.includeEnrichment ? 1.8 : 1;

  let pageMultiplier = 1;
  if (config.pageRange === "1") pageMultiplier = 0.2;
  else if (config.pageRange === "1-3") pageMultiplier = 0.4;
  else if (config.pageRange === "1-5") pageMultiplier = 0.6;

  const totalCost = fileCount * baseCostPerFile * enrichmentMultiplier * pageMultiplier;
  const totalTime = Math.ceil(
    fileCount * baseTimePerFile * enrichmentMultiplier * pageMultiplier
  );

  return {
    cost: `$${totalCost < 0.01 ? "< 0.01" : totalCost.toFixed(2)}`,
    time: totalTime < 60 ? `~${totalTime}s` : `~${Math.ceil(totalTime / 60)}m`,
  };
}

export function ConfigPanel({
  config,
  onChange,
  onRunParse,
  isRunning,
  hasFiles,
  fileCount = 0,
}: ConfigPanelProps) {
  const [sections, setSections] = useState<Record<SectionKey, boolean>>(
    loadSectionState
  );

  const summary = useMemo(() => {
    if (!hasFiles) return null;
    const { cost, time } = estimateCostAndTime(config, fileCount);
    return {
      docType: getDocTypeLabel(config.documentTypeHint),
      pages: getPageLabel(config.pageRange),
      balanceCheck: config.crossCheckBalances,
      enrichment: config.includeEnrichment,
      cost,
      time,
    };
  }, [config, hasFiles, fileCount]);

  const toggle = useCallback((key: SectionKey) => {
    setSections((prev) => {
      const next = { ...prev, [key]: !prev[key] };
      saveSectionState(next);
      return next;
    });
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-gray-200 px-5 py-4">
        <div className="flex items-center gap-2">
          <Settings className="w-4 h-4 text-gray-500" />
          <h2 className="text-sm font-semibold text-gray-900">Configuration</h2>
        </div>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 px-5 py-3 overflow-auto">
        {/* ── Document ── */}
        <SectionHeader
          label="Document"
          isOpen={sections.document}
          onToggle={() => toggle("document")}
        />
        {sections.document && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Document Type
              </label>
              <select
                value={config.documentTypeHint}
                onChange={(e) =>
                  onChange({ ...config, documentTypeHint: e.target.value })
                }
                className="w-full h-9 rounded-lg border border-gray-300 px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent"
              >
                {DOC_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Page Range
              </label>
              <select
                value={config.pageRange}
                onChange={(e) =>
                  onChange({ ...config, pageRange: e.target.value })
                }
                className="w-full h-9 rounded-lg border border-gray-300 px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent"
              >
                {PAGE_RANGE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        <div className="border-t border-gray-100 mt-7" />

        {/* ── Validation ── */}
        <SectionHeader
          label="Validation"
          isOpen={sections.validation}
          onToggle={() => toggle("validation")}
        />
        {sections.validation && (
          <div className="space-y-4">
            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.crossCheckBalances}
                  onChange={(e) =>
                    onChange({ ...config, crossCheckBalances: e.target.checked })
                  }
                  className="h-[18px] w-[18px] rounded border-[1.5px] border-gray-300 accent-gray-800 focus:ring-gray-800"
                />
                <span className="text-sm text-gray-700">Cross-check balances</span>
              </label>
              <p className="text-xs text-gray-500 mt-1 ml-[26px]">
                Verify beginning + credits &minus; debits = ending balance
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-sm font-medium text-gray-700">
                  Confidence threshold
                </label>
                <span className="text-xs tabular-nums text-gray-500">
                  {Math.round(config.confidenceThreshold * 100)}%
                </span>
              </div>
              <input
                type="range"
                min={0.5}
                max={1}
                step={0.05}
                value={config.confidenceThreshold}
                onChange={(e) =>
                  onChange({
                    ...config,
                    confidenceThreshold: parseFloat(e.target.value),
                  })
                }
                className="w-full accent-gray-800"
              />
              <div className="flex justify-between text-[10px] text-gray-400 mt-0.5">
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={config.flagDuplicates}
                onChange={(e) =>
                  onChange({ ...config, flagDuplicates: e.target.checked })
                }
                className="h-[18px] w-[18px] rounded border-[1.5px] border-gray-300 accent-gray-800 focus:ring-gray-800"
              />
              <span className="text-sm text-gray-700">Flag duplicates</span>
            </label>
          </div>
        )}

        <div className="border-t border-gray-100 mt-7" />

        {/* ── Enrichment ── */}
        <SectionHeader
          label="Enrichment"
          isOpen={sections.enrichment}
          onToggle={() => toggle("enrichment")}
        />
        {sections.enrichment && (
          <div className="space-y-4">
            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.includeEnrichment}
                  onChange={(e) =>
                    onChange({ ...config, includeEnrichment: e.target.checked })
                  }
                  className="h-[18px] w-[18px] rounded border-[1.5px] border-gray-300 accent-gray-800 focus:ring-gray-800"
                />
                <span className="text-sm text-gray-700">
                  Include AI Enrichment
                </span>
              </label>
              <p className="text-xs text-gray-500 mt-1 ml-6">
                Adds 25+ financial risk indicators via Gemini
              </p>
            </div>

            {config.includeEnrichment && (
              <div className="space-y-3 pl-1 border-l-2 border-gray-300 ml-2">
                <div className="pl-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Business Name
                  </label>
                  <input
                    type="text"
                    value={config.businessName}
                    onChange={(e) =>
                      onChange({ ...config, businessName: e.target.value })
                    }
                    placeholder="e.g. Acme Corp"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent"
                  />
                </div>
                <div className="pl-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Industry
                  </label>
                  <input
                    type="text"
                    value={config.industry}
                    onChange={(e) =>
                      onChange({ ...config, industry: e.target.value })
                    }
                    placeholder="e.g. Restaurant, Retail"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Anonymization mode
              </label>
              <select
                value={config.anonymizationMode}
                onChange={(e) =>
                  onChange({ ...config, anonymizationMode: e.target.value })
                }
                className="w-full h-9 rounded-lg border border-gray-300 px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent"
              >
                {ANON_MODES.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Redact PII from extracted output.
              </p>
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={config.currencyNormalization}
                onChange={(e) =>
                  onChange({
                    ...config,
                    currencyNormalization: e.target.checked,
                  })
                }
                className="h-[18px] w-[18px] rounded border-[1.5px] border-gray-300 accent-gray-800 focus:ring-gray-800"
              />
              <span className="text-sm text-gray-700">
                Currency normalization
              </span>
            </label>
          </div>
        )}
      </div>

      {/* Parse Summary + Footer */}
      <div className="border-t border-gray-200 p-4 space-y-3">
        <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50/50 px-3.5 py-3">
          {summary ? (
            <ul className="space-y-1 font-mono text-xs text-gray-600">
              <li className="flex items-start gap-1.5">
                <span className="text-gray-400 select-none">&rarr;</span>
                {summary.docType}
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-gray-400 select-none">&rarr;</span>
                Pages: {summary.pages}
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-gray-400 select-none">&rarr;</span>
                Validation: Balance check {summary.balanceCheck ? "ON" : "OFF"}
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-gray-400 select-none">&rarr;</span>
                Enrichment: {summary.enrichment ? "ON" : "OFF"}
              </li>
              <li className="flex items-start gap-1.5 pt-1 border-t border-gray-200 mt-1">
                <span className="text-gray-400 select-none">&rarr;</span>
                Est. cost: {summary.cost} &middot; {summary.time}
              </li>
            </ul>
          ) : (
            <p className="text-xs text-gray-400 text-center">
              Upload a file to see estimate
            </p>
          )}
        </div>

        <button
          onClick={onRunParse}
          disabled={!hasFiles || isRunning}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gray-800 text-white text-sm font-medium hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Play className="w-4 h-4" />
          {isRunning ? "Parsing..." : "Run Parse"}
        </button>
      </div>
    </div>
  );
}
