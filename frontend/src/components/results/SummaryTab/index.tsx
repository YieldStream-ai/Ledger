import { useState } from "react";
import { clsx } from "clsx";
import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import type { ParseResponse, TemplateMatchResult } from "../../../api/types";
import styles from "./SummaryTab.module.css";

interface SummaryTabProps {
  result: ParseResponse;
}

function ConfidenceBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className={styles.confidenceBarWrapper}>
      <div className={styles.confidenceBarHeader}>
        <span className={styles.confidenceLabel}>{label}</span>
        <span
          className={clsx(
            styles.confidenceValue,
            pct >= 70 ? styles.confidenceHigh : pct >= 40 ? styles.confidenceMid : styles.confidenceLow
          )}
        >
          {pct}%
        </span>
      </div>
      <div className={styles.confidenceTrack}>
        <div
          className={clsx(
            styles.confidenceFill,
            pct >= 70 ? styles.confidenceFillHigh : pct >= 40 ? styles.confidenceFillMid : styles.confidenceFillLow
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
      className={styles.templateBadge}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span
        className={clsx(
          styles.templateBadgeLabel,
          isLowConfidence ? styles.templateBadgeLow : styles.templateBadgeHigh
        )}
      >
        {label}
      </span>

      {showTooltip && (
        <div className={styles.templateTooltip}>
          <p className={styles.tooltipTitle}>
            Template: {match.id} ({pct}% confidence)
          </p>

          {match.signals.length > 0 && (
            <div className={styles.tooltipList}>
              <p className={styles.tooltipSectionLabel}>Signals matched:</p>
              <ul>
                {match.signals.map((s, i) => (
                  <li key={i} className={styles.tooltipSignalRow}>
                    <span className={styles.tooltipSignalCategory}>{s.category}</span>
                    <span>{s.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {match.alternatives.length > 0 && (
            <div>
              <p className={styles.tooltipSectionLabel}>Alternatives considered:</p>
              <ul className={styles.tooltipList}>
                {match.alternatives.map((a) => (
                  <li key={a.id} className={styles.tooltipAltRow}>
                    <span>{a.bank_name}</span>
                    <span className={styles.tooltipAltConfidence}>{Math.round(a.confidence * 100)}%</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {match.fallback_used && (
            <p className={styles.tooltipFallbackWarning}>
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
    <div className={styles.container}>
      {/* Status */}
      {result.status === "error" && (
        <div className={styles.errorBanner}>
          <XCircle className={styles.errorIcon} />
          <div>
            <p className={styles.errorTitle}>Parse Error</p>
            <p className={styles.errorMessage}>{result.error}</p>
          </div>
        </div>
      )}

      {/* Classification */}
      {result.classification && (
        <div className={styles.classificationRow}>
          <span className={styles.docTypeBadge}>
            {result.classification.document_type.replace(/_/g, " ")}
          </span>
          <span className={styles.methodLabel}>
            via {result.classification.method} ({Math.round(result.classification.confidence * 100)}%)
          </span>
          {result.metadata?.needs_human_review && (
            <span className={styles.reviewBadge}>
              <AlertTriangle className={styles.reviewIcon} />
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
            styles.qualityGate,
            result.quality.passed ? styles.qualityPassed : styles.qualityFailed
          )}
        >
          {result.quality.passed ? (
            <CheckCircle2 className={styles.qualityIcon} />
          ) : (
            <XCircle className={styles.qualityIcon} />
          )}
          Quality: {result.quality.overall_score}/100
          {result.quality.issues.length > 0 && (
            <span className={styles.qualityIssues}>Issues: {result.quality.issues.join(", ")}</span>
          )}
        </div>
      )}

      {/* Arithmetic Validation */}
      {result.validation && result.validation.balance_check === "failed" && (
        <div className={styles.balanceWarning}>
          <AlertTriangle className={styles.balanceWarningIcon} />
          <div>
            <p className={styles.balanceWarningTitle}>Balance Discrepancy Detected</p>
            <p className={styles.balanceWarningDetail}>
              Expected ending balance: ${result.validation.expected_ending.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              {" | "}Actual: ${result.validation.actual_ending.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              {" | "}Discrepancy: ${result.validation.discrepancy.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      )}
      {result.validation && result.validation.balance_check === "passed" && (
        <div className={styles.balancePassed}>
          <CheckCircle2 className={styles.qualityIcon} />
          Balance cross-check passed (confidence: {Math.round(result.validation.confidence * 100)}%)
        </div>
      )}

      {/* Confidence Scores */}
      {result.confidence && (
        <div className={styles.confidenceSection}>
          <h3 className={styles.confidenceTitle}>Confidence Scores</h3>
          <ConfidenceBar label="Overall" value={result.confidence.overall} />
          <ConfidenceBar label="Text Quality" value={result.confidence.text_quality} />
          <ConfidenceBar label="Table Extraction" value={result.confidence.table_extraction} />
          <ConfidenceBar label="Template Match" value={result.confidence.template_match} />
        </div>
      )}

      {/* Parsed Fields */}
      {data && (
        <div>
          <h3 className={styles.fieldsTitle}>Extracted Fields</h3>
          <div className={styles.fieldsGrid}>
            {DISPLAY_FIELDS.map((field) => {
              const val = data[field.key];
              const isMissing = val === null || val === undefined;
              return (
                <div key={field.key} className={styles.fieldRow}>
                  <span className={styles.fieldLabel}>{field.label}</span>
                  <span
                    className={clsx(
                      styles.fieldValue,
                      isMissing && styles.fieldValueMissing
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
        <div className={styles.metadata}>
          <p>Method: {result.extraction_method} | Pages: {result.page_count} | Time: {result.processing_time_ms}ms</p>
          {result.metadata.template_used && (
            <p>Template: {result.metadata.template_used} | Bank: {result.metadata.bank_detected || "unknown"}</p>
          )}
          {result.metadata.fields_missing.length > 0 && (
            <p className={styles.metadataMissing}>
              Missing fields: {result.metadata.fields_missing.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
