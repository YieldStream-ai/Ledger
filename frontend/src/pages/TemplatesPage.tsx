import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Layers, ChevronDown, ChevronRight } from "lucide-react";
import { clsx } from "clsx";
import { getBankTemplates } from "../api/client";
import type { TemplateDetail } from "../api/types";

export function TemplatesPage() {
  const { data: templates = [], isLoading } = useQuery<TemplateDetail[]>({
    queryKey: ["bankTemplates"],
    queryFn: getBankTemplates,
  });
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const sorted = [...templates].sort(
    (a, b) => b.match_count_30d - a.match_count_30d
  );

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="border-b border-gray-200 px-6 py-4 flex items-center gap-2">
        <Layers className="w-5 h-5 text-purple-500" />
        <h2 className="text-sm font-semibold text-gray-900">
          Bank Templates ({templates.length})
        </h2>
      </div>

      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="w-6 h-6 border-2 border-gray-200 border-t-gray-600 rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs text-gray-500 uppercase tracking-wider">
                <th className="px-6 py-3 font-medium w-8" />
                <th className="px-6 py-3 font-medium">Template</th>
                <th className="px-6 py-3 font-medium">Bank</th>
                <th className="px-6 py-3 font-medium text-right">Signals</th>
                <th className="px-6 py-3 font-medium text-right">
                  Matches (30d)
                </th>
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
      <tr
        onClick={onToggle}
        className="border-b border-gray-50 hover:bg-gray-50 transition-colors cursor-pointer"
      >
        <td className="pl-6 py-3 text-gray-400">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </td>
        <td className="px-6 py-3">
          <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded text-purple-700">
            {template.id}
          </code>
        </td>
        <td className="px-6 py-3 text-gray-900 font-medium">
          {template.bank_name}
        </td>
        <td className="px-6 py-3 text-right text-gray-600 tabular-nums">
          {template.signal_count}
        </td>
        <td className="px-6 py-3 text-right tabular-nums">
          <span
            className={clsx(
              "inline-flex items-center justify-center min-w-[2rem] px-2 py-0.5 rounded-full text-xs font-medium",
              template.match_count_30d > 0
                ? "bg-purple-100 text-purple-700"
                : "bg-gray-100 text-gray-400"
            )}
          >
            {template.match_count_30d}
          </span>
        </td>
      </tr>
      {isExpanded && (
        <tr className="bg-gray-50">
          <td />
          <td colSpan={4} className="px-6 py-3">
            <p className="text-xs text-gray-500 mb-2 font-medium">
              Match signals:
            </p>
            <div className="grid grid-cols-2 gap-1.5">
              {template.signals.map((s, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 text-xs text-gray-600"
                >
                  <span className="px-1.5 py-0.5 rounded bg-gray-200 text-gray-500 text-[10px] font-mono">
                    {s.category}
                  </span>
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
