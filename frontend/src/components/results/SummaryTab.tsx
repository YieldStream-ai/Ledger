import { useState } from "react";
import { clsx } from "clsx";
import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import type { ParseResponse, TemplateMatchResult } from "../../api/types";

interface SummaryTabProps {
  result: ParseResponse;
}

function ConfidenceBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-600">{label}</span>
        <span
          className={clsx(
            "font-medium",
            pct >= 70 ? "text-green-600" : pct >= 40 ? "text-yellow-600" : "text-red-600"
          )}
        >
          {pct}%
        </span>
      </div>
      <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={clsx(
            "h-full rounded-full transition-all",
            pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-yellow-500" : "bg-red-500"
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "--";
  if (typeof value === "number") {
    if (Math.abs(value) >= 100) return value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return String(value);
  }
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

const DISPLAY_FIELDS = [
  { key: "bank_name", label: "Bank" },
  { key: "account_holder", label: "Account Holder" },
  { key: "account_number_last4", label: "Account (last 4)" },
  { key: "period_start", label: "Period Start" },
  { key: "period_end", label: "Period End" },
  { key: "beginning_balance", label: "Beginning Balance", prefix: "$" },
  { key: "ending_balance", label: "Ending Balance", prefix: "$" },
  { key: "total_deposits", label: "Total Deposits", prefix: "$" },
  { key: "total_withdrawals", label: "Total Withdrawals", prefix: "$" },
  { key: "deposit_count", label: "Deposit Count" },
  { key: "nsf_count", label: "NSF Count" },
  { key: "average_daily_balance", label: "Average Daily Balance", prefix: "$" },
];

function TemplateMatchBadge({ match }: { match: TemplateMatchResult }) {
  const [showTooltip, setShowTooltip] = useState(false);
  const pct = Math.round(match.confidence * 100);
  const isLowConfidence = match.fallback_used || match.confidence < 0.7;

  const label = isLowConfidence
    ? `Generic Parser \u00b7 Reduced Accuracy`
    : `Matched: ${match.bank_name} \u00b7 ${pct}%`;

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span
        className={clsx(
          "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium cursor-default",
          isLowConfidence
            ? "bg-amber-100 text-amber-700"
            : "bg-purple-100 text-purple-700"
        )}
      >
        {label}
      </span>

      {showTooltip && (
        <div className="absolute z-50 top-full left-0 mt-2 w-72 bg-gray-900 text-gray-100 rounded-lg shadow-xl p-3 text-xs">
          <p className="font-medium mb-2">
            Template: {match.id} ({pct}% confidence)
          </p>

          {match.signals.length > 0 && (
            <div className="mb-2">
              <p className="text-gray-400 mb-1">Signals matched:</p>
              <ul className="space-y-0.5">
                {match.signals.map((s, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-gray-500 shrink-0">{s.category}</span>
                    <span>{s.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {match.alternatives.length > 0 && (
            <div>
              <p className="text-gray-400 mb-1">Alternatives considered:</p>
              <ul className="space-y-0.5">
                {match.alternatives.map((a) => (
                  <li key={a.id} className="flex justify-between">
                    <span>{a.bank_name}</span>
                    <span className="text-gray-400">{Math.round(a.confidence * 100)}%</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {match.fallback_used && (
            <p className="mt-2 text-amber-400">
              No template matched above 70% confidence. Using generic parser with reduced accuracy.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export function SummaryTab({ result }: SummaryTabProps) {
  const data = result.parsed_data;

  return (
    <div className="space-y-6">
      {/* Status */}
      {result.status === "error" && (
        <div className="flex items-start gap-3 p-4 rounded-lg bg-red-50 text-red-800">
          <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Parse Error</p>
            <p className="text-sm mt-1">{result.error}</p>
          </div>
        </div>
      )}

      {/* Classification */}
      {result.classification && (
        <div className="flex items-center gap-3">
          <span className="px-2.5 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
            {result.classification.document_type.replace(/_/g, " ")}
          </span>
          <span className="text-xs text-gray-500">
            via {result.classification.method} ({Math.round(result.classification.confidence * 100)}%)
          </span>
          {result.metadata?.needs_human_review && (
            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-yellow-100 text-yellow-700 text-xs">
              <AlertTriangle className="w-3 h-3" />
              Needs Review
            </span>
          )}
        </div>
      )}

      {/* Template Match Badge */}
      {result.template_match && (
        <TemplateMatchBadge match={result.template_match} />
      )}

      {/* Quality Gate */}
      {result.quality && (
        <div
          className={clsx(
            "flex items-center gap-2 px-3 py-2 rounded-lg text-xs",
            result.quality.passed
              ? "bg-green-50 text-green-700"
              : "bg-red-50 text-red-700"
          )}
        >
          {result.quality.passed ? (
            <CheckCircle2 className="w-4 h-4" />
          ) : (
            <XCircle className="w-4 h-4" />
          )}
          Quality: {result.quality.overall_score}/100
          {result.quality.issues.length > 0 && (
            <span className="ml-2">Issues: {result.quality.issues.join(", ")}</span>
          )}
        </div>
      )}

      {/* Arithmetic Validation */}
      {result.validation && result.validation.balance_check === "failed" && (
        <div className="flex items-start gap-3 p-4 rounded-lg bg-yellow-50 border border-yellow-200 text-yellow-800">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Balance Discrepancy Detected</p>
            <p className="text-sm mt-1">
              Expected ending balance: ${result.validation.expected_ending.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              {" | "}Actual: ${result.validation.actual_ending.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              {" | "}Discrepancy: ${result.validation.discrepancy.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      )}
      {result.validation && result.validation.balance_check === "passed" && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs bg-green-50 text-green-700">
          <CheckCircle2 className="w-4 h-4" />
          Balance cross-check passed (confidence: {Math.round(result.validation.confidence * 100)}%)
        </div>
      )}

      {/* Confidence Scores */}
      {result.confidence && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-medium text-gray-900">Confidence Scores</h3>
          <ConfidenceBar label="Overall" value={result.confidence.overall} />
          <ConfidenceBar label="Text Quality" value={result.confidence.text_quality} />
          <ConfidenceBar label="Table Extraction" value={result.confidence.table_extraction} />
          <ConfidenceBar label="Template Match" value={result.confidence.template_match} />
        </div>
      )}

      {/* Parsed Fields */}
      {data && (
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">Extracted Fields</h3>
          <div className="grid grid-cols-2 gap-x-6 gap-y-2">
            {DISPLAY_FIELDS.map((field) => {
              const val = data[field.key];
              const isMissing = val === null || val === undefined;
              return (
                <div key={field.key} className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-xs text-gray-500">{field.label}</span>
                  <span
                    className={clsx(
                      "text-sm font-medium",
                      isMissing ? "text-gray-300" : "text-gray-900"
                    )}
                  >
                    {isMissing
                      ? "--"
                      : `${field.prefix || ""}${formatValue(val)}`}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Metadata */}
      {result.metadata && (
        <div className="text-xs text-gray-500 space-y-1">
          <p>Method: {result.extraction_method} | Pages: {result.page_count} | Time: {result.processing_time_ms}ms</p>
          {result.metadata.template_used && (
            <p>Template: {result.metadata.template_used} | Bank: {result.metadata.bank_detected || "unknown"}</p>
          )}
          {result.metadata.fields_missing.length > 0 && (
            <p className="text-yellow-600">
              Missing fields: {result.metadata.fields_missing.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
