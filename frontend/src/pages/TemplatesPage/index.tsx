import { useState, useMemo, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Layers, ChevronDown, ChevronRight } from "lucide-react";
import { clsx } from "clsx";
import { getBankTemplates } from "../../api/client";
import type { TemplateDetail } from "../../api/types";
import type { TemplatesSortKey } from "../../components/config/TemplatesConfigPanel";
import styles from "./TemplatesPage.module.css";

interface TemplatesPageProps {
  bankFilter: string;
  sortBy: TemplatesSortKey;
  onBankNamesLoaded: (names: string[]) => void;
}

export function TemplatesPage({ bankFilter, sortBy, onBankNamesLoaded }: TemplatesPageProps) {
  const { data: templates = [], isLoading } = useQuery<TemplateDetail[]>({
    queryKey: ["bankTemplates"],
    queryFn: getBankTemplates,
  });
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const bankNames = useMemo(
    () => [...new Set(templates.map((t) => t.bank_name))].sort(),
    [templates]
  );

  useEffect(() => {
    if (bankNames.length > 0) onBankNamesLoaded(bankNames);
  }, [bankNames, onBankNamesLoaded]);

  const filtered = bankFilter
    ? templates.filter((t) => t.bank_name === bankFilter)
    : templates;

  const sorted = useMemo(() => {
    const list = [...filtered];
    switch (sortBy) {
      case "match_count":
        return list.sort((a, b) => b.match_count_30d - a.match_count_30d);
      case "confidence":
        return list.sort((a, b) => b.signal_count - a.signal_count);
      case "last_used":
        return list.sort((a, b) => b.match_count_30d - a.match_count_30d);
      default:
        return list;
    }
  }, [filtered, sortBy]);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Layers className={styles.headerIcon} />
        <h2 className={styles.headerTitle}>
          Bank Templates ({templates.length})
        </h2>
      </div>

      <div className={styles.tableWrapper}>
        {isLoading ? (
          <div className={styles.loadingWrapper}>
            <div className={styles.spinner} />
          </div>
        ) : (
          <table className={styles.table}>
            <thead className={styles.tableHead}>
              <tr>
                <th className={styles.colExpand} />
                <th>Template</th>
                <th>Bank</th>
                <th className={styles.colRight}>Signals</th>
                <th className={styles.colRight}>Matches (30d)</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((t) => {
                const isExpanded = expandedId === t.id;
                return (
                  <TemplateRow
                    key={t.id}
                    template={t}
                    isExpanded={isExpanded}
                    onToggle={() =>
                      setExpandedId(isExpanded ? null : t.id)
                    }
                  />
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function TemplateRow({
  template,
  isExpanded,
  onToggle,
}: {
  template: TemplateDetail;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <tr onClick={onToggle} className={styles.row}>
        <td className={styles.expandCell}>
          {isExpanded ? (
            <ChevronDown className={styles.expandIcon} />
          ) : (
            <ChevronRight className={styles.expandIcon} />
          )}
        </td>
        <td className={styles.templateIdCell}>
          <code className={styles.templateIdCode}>{template.id}</code>
        </td>
        <td className={styles.bankNameCell}>{template.bank_name}</td>
        <td className={styles.signalCountCell}>{template.signal_count}</td>
        <td className={styles.matchCountCell}>
          <span
            className={clsx(
              styles.matchBadge,
              template.match_count_30d > 0
                ? styles.matchBadgeActive
                : styles.matchBadgeInactive
            )}
          >
            {template.match_count_30d}
          </span>
        </td>
      </tr>
      {isExpanded && (
        <tr className={styles.expandedRow}>
          <td />
          <td colSpan={4} className={styles.expandedContent}>
            <p className={styles.signalsLabel}>Match signals:</p>
            <div className={styles.signalsGrid}>
              {template.signals.map((s, i) => (
                <div key={i} className={styles.signalItem}>
                  <span className={styles.signalCategory}>{s.category}</span>
                  <span>{s.description}</span>
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
