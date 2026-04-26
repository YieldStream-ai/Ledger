import { Plus, Settings } from "lucide-react";

export type TemplatesSortKey = "match_count" | "last_used" | "confidence";

interface TemplatesConfigPanelProps {
  bankFilter: string;
  onBankFilterChange: (value: string) => void;
  bankNames: string[];
  sortBy: TemplatesSortKey;
  onSortByChange: (value: TemplatesSortKey) => void;
  onRegisterNew: () => void;
}

const SORT_OPTIONS: { value: TemplatesSortKey; label: string }[] = [
  { value: "match_count", label: "Match count" },
  { value: "last_used", label: "Last used" },
  { value: "confidence", label: "Confidence" },
];

export function TemplatesConfigPanel({
  bankFilter,
  onBankFilterChange,
  bankNames,
  sortBy,
  onSortByChange,
  onRegisterNew,
}: TemplatesConfigPanelProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-200 px-5 py-4">
        <div className="flex items-center gap-2">
          <Settings className="w-4 h-4 text-gray-500" />
          <h2 className="text-sm font-semibold text-gray-900">Configuration</h2>
        </div>
      </div>

      <div className="flex-1 p-5 space-y-5 overflow-auto">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1.5">
            Filter by bank
          </label>
          <select
            value={bankFilter}
            onChange={(e) => onBankFilterChange(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All banks</option>
            {bankNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1.5">
            Sort by
          </label>
          <select
            value={sortBy}
            onChange={(e) => onSortByChange(e.target.value as TemplatesSortKey)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="border-t border-gray-200 p-4">
        <button
          onClick={onRegisterNew}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Register New Template
        </button>
      </div>
    </div>
  );
}
