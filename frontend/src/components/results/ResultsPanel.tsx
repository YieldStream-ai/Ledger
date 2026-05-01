import { useState } from "react";
import { clsx } from "clsx";
import { SummaryTab } from "./SummaryTab";
import { RawTextTab } from "./RawTextTab";
import { TablesTab } from "./TablesTab";
import { TierLogsTab } from "./TierLogsTab";
import type { ParseResponse } from "../../api/types";

interface ResultsPanelProps {
  result: ParseResponse;
}

const TABS = ["Summary", "Raw Text", "Tables", "Tier Logs"] as const;
type Tab = (typeof TABS)[number];

export function ResultsPanel({ result }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("Summary");

  const availableTabs = TABS.filter((tab) => {
    if (tab === "Tables") return result.tables.length > 0;
    return true;
  });

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-200 px-6">
        <div className="flex gap-1">
          {availableTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={clsx(
                "px-4 py-3 text-sm font-medium border-b-2 transition-colors",
                activeTab === tab
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              )}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {activeTab === "Summary" && <SummaryTab result={result} />}
        {activeTab === "Raw Text" && <RawTextTab text={result.text_content} />}
        {activeTab === "Tables" && <TablesTab tables={result.tables} />}
        {activeTab === "Tier Logs" && <TierLogsTab logs={result.tier_logs} />}
      </div>
    </div>
  );
}
