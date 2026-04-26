import { Play, Settings } from "lucide-react";
import type { ParseConfig } from "../../api/types";

interface ConfigPanelProps {
  config: ParseConfig;
  onChange: (config: ParseConfig) => void;
  onRunParse: () => void;
  isRunning: boolean;
  hasFiles: boolean;
}

const DOC_TYPES = [
  { value: "", label: "Auto-detect" },
  { value: "bank_statement", label: "Bank Statement" },
  { value: "business_tax_return", label: "Business Tax Return" },
  { value: "personal_tax_return", label: "Personal Tax Return" },
  { value: "mca_application", label: "MCA Application" },
];

export function ConfigPanel({
  config,
  onChange,
  onRunParse,
  isRunning,
  hasFiles,
}: ConfigPanelProps) {
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
            Document Type
          </label>
          <select
            value={config.documentTypeHint}
            onChange={(e) =>
              onChange({ ...config, documentTypeHint: e.target.value })
            }
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {DOC_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={config.includeEnrichment}
              onChange={(e) =>
                onChange({ ...config, includeEnrichment: e.target.checked })
              }
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Include AI Enrichment</span>
          </label>
          <p className="text-xs text-gray-500 mt-1 ml-6">
            Adds 25+ financial risk indicators via Gemini
          </p>
        </div>

        {config.includeEnrichment && (
          <div className="space-y-3 pl-1 border-l-2 border-blue-200 ml-2">
            <div className="pl-3">
              <label className="block text-xs font-medium text-gray-700 mb-1.5">
                Business Name
              </label>
              <input
                type="text"
                value={config.businessName}
                onChange={(e) =>
                  onChange({ ...config, businessName: e.target.value })
                }
                placeholder="e.g. Acme Corp"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="pl-3">
              <label className="block text-xs font-medium text-gray-700 mb-1.5">
                Industry
              </label>
              <input
                type="text"
                value={config.industry}
                onChange={(e) =>
                  onChange({ ...config, industry: e.target.value })
                }
                placeholder="e.g. Restaurant, Retail"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 p-4">
        <button
          onClick={onRunParse}
          disabled={!hasFiles || isRunning}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Play className="w-4 h-4" />
          {isRunning ? "Parsing..." : "Run Parse"}
        </button>
      </div>
    </div>
  );
}
