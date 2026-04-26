import { CheckCircle2, XCircle, MinusCircle } from "lucide-react";
import { clsx } from "clsx";
import type { TierLog } from "../../api/types";

interface TierLogsTabProps {
  logs: TierLog[];
}

export function TierLogsTab({ logs }: TierLogsTabProps) {
  if (logs.length === 0) {
    return <p className="text-sm text-gray-500">No tier logs available.</p>;
  }

  return (
    <div className="space-y-1">
      {logs.map((log, i) => {
        const icon =
          log.status === "success" ? (
            <CheckCircle2 className="w-5 h-5 text-green-500" />
          ) : log.status === "failed" ? (
            <XCircle className="w-5 h-5 text-red-500" />
          ) : (
            <MinusCircle className="w-5 h-5 text-gray-400" />
          );

        return (
          <div key={i} className="flex items-start gap-3">
            {/* Timeline line */}
            <div className="flex flex-col items-center">
              {icon}
              {i < logs.length - 1 && (
                <div className="w-px h-8 bg-gray-200 my-1" />
              )}
            </div>

            <div
              className={clsx(
                "flex-1 rounded-lg p-3 text-sm",
                log.status === "success" ? "bg-green-50" : log.status === "failed" ? "bg-red-50" : "bg-gray-50"
              )}
            >
              <div className="flex justify-between items-center">
                <span className="font-medium text-gray-900">
                  Tier {log.tier_order}: {log.tier}
                </span>
                <span className="text-xs text-gray-500">
                  {log.processing_time_ms}ms
                </span>
              </div>
              <div className="mt-1 text-xs text-gray-600 space-x-4">
                <span>Chars: {log.text_char_count.toLocaleString()}</span>
                <span>Tables: {log.table_count}</span>
                <span>Confidence: {Math.round(log.confidence_score * 100)}%</span>
              </div>
              {log.failure_reason && (
                <p className="mt-1 text-xs text-red-600">{log.failure_reason}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
