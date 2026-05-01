import { useState } from "react";
import { clsx } from "clsx";
import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import type {
  CashFlow,
  Debt,
  Expenses,
  Identity,
  ParseResponse,
  Period,
  Revenue,
  TemplateMatchResult,
} from "../../../api/types";
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

function fmtMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return "--";
  return `$${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "--";
  return value.toLocaleString("en-US");
}

function fmtPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "--";
  return `${(value * 100).toFixed(1)}%`;
}

function fmtText(value: string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "--";
  return value;
}

interface FieldDef {
  label: string;
  value: string;
}

function FieldGrid({ fields }: { fields: FieldDef[] }) {
  return (
    <div className={styles.fieldsGrid}>
      {fields.map((f) => (
        <div key={f.label} className={styles.fieldRow}>
          <span className={styles.fieldLabel}>{f.label}</span>
          <span className={clsx(styles.fieldValue, f.value === "--" && styles.fieldValueMissing)}>
            {f.value}
          </span>
        </div>
      ))}
    </div>
  );
}

function NamespaceSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className={styles.fieldsTitle}>{title}</h3>
      {children}
    </div>
  );
}

function IdentitySection({ identity }: { identity: Identity }) {
  return (
    <NamespaceSection title="Identity">
      <FieldGrid
        fields={[
          { label: "Account Holder", value: fmtText(identity.account_holder_name) },
          { label: "Account (last 4)", value: fmtText(identity.account_number_last4) },
          { label: "Business Name", value: fmtText(identity.business_name) },
          { label: "Address", value: fmtText(identity.address) },
          { label: "EIN", value: fmtText(identity.ein) },
          { label: "Consistency Check", value: fmtText(identity.consistency_check) },
        ]}
      />
    </NamespaceSection>
  );
}

function PeriodSection({ period }: { period: Period }) {
  return (
    <NamespaceSection title="Period">
      <FieldGrid
        fields={[
          { label: "Start", value: fmtText(period.start) },
          { label: "End", value: fmtText(period.end) },
        ]}
      />
    </NamespaceSection>
  );
}

function CashFlowSection({ cashFlow }: { cashFlow: CashFlow }) {
  return (
    <NamespaceSection title="Cash Flow">
      <FieldGrid
        fields={[
          { label: "Starting Balance", value: fmtMoney(cashFlow.starting_balance) },
          { label: "Ending Balance", value: fmtMoney(cashFlow.ending_balance) },
          { label: "Total Inflows", value: fmtMoney(cashFlow.total_inflows) },
          { label: "Total Outflows", value: fmtMoney(cashFlow.total_outflows) },
          { label: "Net Change", value: fmtMoney(cashFlow.net_change) },
          { label: "Avg Daily Balance", value: fmtMoney(cashFlow.average_daily_balance) },
          { label: "Min Balance", value: fmtMoney(cashFlow.min_balance) },
          { label: "Min Balance Date", value: fmtText(cashFlow.min_balance_date) },
          { label: "Negative Balance Days", value: fmtNumber(cashFlow.negative_balance_days) },
          { label: "NSF Count", value: fmtNumber(cashFlow.nsf_count) },
          { label: "Overdraft Events", value: fmtNumber(cashFlow.overdraft_events.length) },
          { label: "Daily Balance Days", value: fmtNumber(Object.keys(cashFlow.daily_balances).length) },
        ]}
      />
    </NamespaceSection>
  );
}

function RevenueSection({ revenue }: { revenue: Revenue }) {
  return (
    <NamespaceSection title="Revenue">
      <FieldGrid
        fields={[
          { label: "Gross Deposits", value: fmtMoney(revenue.gross_deposits) },
          { label: "Deposit Count", value: fmtNumber(revenue.deposit_count) },
          { label: "Non-Processor Inflows", value: fmtMoney(revenue.non_processor_inflows) },
          { label: "Recurring Revenue Est.", value: fmtMoney(revenue.recurring_revenue_estimate) },
          { label: "Processor Deposits", value: fmtNumber(revenue.processor_deposits.length) },
          { label: "Chargeback Count", value: fmtNumber(revenue.chargebacks.count) },
          { label: "Chargeback Total", value: fmtMoney(revenue.chargebacks.total) },
          { label: "Top Counterparty", value: fmtPct(revenue.concentration.top_counterparty_percent) },
          { label: "Top 5", value: fmtPct(revenue.concentration.top_5_percent) },
          { label: "Seasonality Signal", value: fmtText(revenue.seasonality_signal) },
        ]}
      />
    </NamespaceSection>
  );
}

function DebtSection({ debt }: { debt: Debt }) {
  return (
    <NamespaceSection title="Debt">
      <FieldGrid
        fields={[
          { label: "Active Positions", value: fmtNumber(debt.active_positions.length) },
          { label: "DSCR", value: debt.dscr === null ? "--" : debt.dscr.toFixed(2) },
          { label: "Stacking Burden", value: fmtPct(debt.stacking_burden_pct) },
          { label: "Daily Debt Service", value: fmtMoney(debt.total_daily_debt_service) },
          { label: "Monthly Debt Service", value: fmtMoney(debt.total_monthly_debt_service) },
          { label: "Lien Flags", value: fmtNumber(debt.lien_flags.length) },
        ]}
      />
      {debt.active_positions.length > 0 && (
        <div className={styles.metadata} style={{ marginTop: "0.5rem" }}>
          {debt.active_positions.map((pos, i) => (
            <p key={i}>
              {pos.lender_name || "Unknown lender"}
              {pos.type ? ` (${pos.type})` : ""}
              {pos.daily_debit !== null ? ` — ${fmtMoney(pos.daily_debit)}/day` : ""}
              {pos.monthly_payment !== null ? ` — ${fmtMoney(pos.monthly_payment)}/mo` : ""}
              {pos.estimated_balance !== null ? ` — bal ${fmtMoney(pos.estimated_balance)}` : ""}
            </p>
          ))}
        </div>
      )}
    </NamespaceSection>
  );
}

function ExpensesSection({ expenses }: { expenses: Expenses }) {
  return (
    <NamespaceSection title="Expenses">
      <FieldGrid
        fields={[
          { label: "Payroll", value: fmtMoney(expenses.payroll.monthly_total) },
          { label: "Rent", value: fmtMoney(expenses.rent.monthly_total) },
          { label: "Utilities", value: fmtMoney(expenses.utilities.monthly_total) },
          { label: "Insurance", value: fmtMoney(expenses.insurance.monthly_total) },
          { label: "Software", value: fmtMoney(expenses.software_subscriptions.monthly_total) },
          { label: "Tax (Federal)", value: fmtMoney(expenses.tax_payments.federal) },
          { label: "Tax (State)", value: fmtMoney(expenses.tax_payments.state) },
          { label: "Tax Last Seen", value: fmtText(expenses.tax_payments.last_seen) },
        ]}
      />
    </NamespaceSection>
  );
}

function TemplateMatchBadge({ match }: { match: TemplateMatchResult }) {
  const [showTooltip, setShowTooltip] = useState(false);
  const pct = Math.round(match.confidence * 100);
  const isLowConfidence = match.fallback_used || match.confidence < 0.7;

  const label = isLowConfidence
    ? `Generic Parser · Reduced Accuracy`
    : `Matched: ${match.bank_name} · ${pct}%`;

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
  const isBankStatement =
    result.classification?.document_type === "bank_statement" && result.cash_flow !== null;

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

      {result.template_match && <TemplateMatchBadge match={result.template_match} />}

      {/* Quality Gate */}
      {result.quality && (
        <div className={clsx(styles.qualityGate, result.quality.passed ? styles.qualityPassed : styles.qualityFailed)}>
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
      {result.validation?.balance_check === "failed" && (
        <div className={styles.balanceWarning}>
          <AlertTriangle className={styles.balanceWarningIcon} />
          <div>
            <p className={styles.balanceWarningTitle}>Balance Discrepancy Detected</p>
            <p className={styles.balanceWarningDetail}>
              Expected: {fmtMoney(result.validation.expected_ending)} | Actual:{" "}
              {fmtMoney(result.validation.actual_ending)} | Discrepancy:{" "}
              {fmtMoney(result.validation.discrepancy)}
            </p>
          </div>
        </div>
      )}
      {result.validation?.balance_check === "passed" && (
        <div className={styles.balancePassed}>
          <CheckCircle2 className={styles.qualityIcon} />
          Balance cross-check passed
        </div>
      )}

      {/* Confidence Scores */}
      {result.confidence && (
        <div className={styles.confidenceSection}>
          <h3 className={styles.confidenceTitle}>Confidence</h3>
          <ConfidenceBar label="Overall" value={result.confidence.overall} />
          <ConfidenceBar label="Text Quality" value={result.confidence.text_quality} />
          <ConfidenceBar label="Table Extraction" value={result.confidence.table_extraction} />
          <ConfidenceBar label="Template Match" value={result.confidence.template_match} />
          {isBankStatement && (
            <>
              <h3 className={styles.confidenceTitle} style={{ marginTop: "0.5rem" }}>
                By Category
              </h3>
              <ConfidenceBar label="Cash Flow" value={result.confidence.by_category.cash_flow} />
              <ConfidenceBar label="Revenue" value={result.confidence.by_category.revenue} />
              <ConfidenceBar label="Debt" value={result.confidence.by_category.debt} />
              <ConfidenceBar label="Expenses" value={result.confidence.by_category.expenses} />
              <ConfidenceBar label="Identity" value={result.confidence.by_category.identity} />
            </>
          )}
        </div>
      )}

      {/* Underwriter namespaces (bank statements) */}
      {isBankStatement && result.identity && <IdentitySection identity={result.identity} />}
      {isBankStatement && result.period && <PeriodSection period={result.period} />}
      {isBankStatement && result.cash_flow && <CashFlowSection cashFlow={result.cash_flow} />}
      {isBankStatement && result.revenue && <RevenueSection revenue={result.revenue} />}
      {isBankStatement && result.debt && <DebtSection debt={result.debt} />}
      {isBankStatement && result.expenses && <ExpensesSection expenses={result.expenses} />}

      {/* Legacy parsed_data — non-bank-statement docs (tax returns, MCA apps) */}
      {!isBankStatement && result.parsed_data && (
        <NamespaceSection title="Extracted Fields">
          <FieldGrid
            fields={Object.entries(result.parsed_data).map(([k, v]) => ({
              label: k.replace(/_/g, " "),
              value:
                v === null || v === undefined
                  ? "--"
                  : typeof v === "number"
                  ? fmtNumber(v)
                  : String(v),
            }))}
          />
        </NamespaceSection>
      )}

      {/* Metadata */}
      {result.metadata && (
        <div className={styles.metadata}>
          <p>
            Method: {result.extraction_method} | Pages: {result.page_count} | Time: {result.processing_time_ms}ms
          </p>
          {result.metadata.template_used && (
            <p>
              Template: {result.metadata.template_used} | Bank: {result.metadata.bank_detected || "unknown"}
            </p>
          )}
          {result.metadata.fields_missing.length > 0 && (
            <p className={styles.metadataMissing}>Missing fields: {result.metadata.fields_missing.join(", ")}</p>
          )}
        </div>
      )}
    </div>
  );
}
