import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2, AlertTriangle, InboxIcon } from "lucide-react";
import { getReviewQueue, clearReviewQueue, removeReviewItem } from "../api/client";
import type { ReviewItem } from "../api/types";

export function ReviewPage() {
  const queryClient = useQueryClient();
  const { data: items = [], isLoading } = useQuery<ReviewItem[]>({
    queryKey: ["reviewQueue"],
    queryFn: getReviewQueue,
    refetchInterval: 10_000,
  });

  const handleClearAll = async () => {
    await clearReviewQueue();
    queryClient.invalidateQueries({ queryKey: ["reviewQueue"] });
  };

  const handleRemove = async (id: string) => {
    await removeReviewItem(id);
    queryClient.invalidateQueries({ queryKey: ["reviewQueue"] });
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-yellow-500" />
          <h2 className="text-sm font-semibold text-gray-900">
            Needs Review ({items.length})
          </h2>
        </div>
        {items.length > 0 && (
          <button
            onClick={handleClearAll}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear All
          </button>
        )}
      </div>

      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="w-6 h-6 border-2 border-gray-200 border-t-gray-600 rounded-full animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <InboxIcon className="w-10 h-10 mb-3" />
            <p className="text-sm">No items need review</p>
            <p className="text-xs mt-1">
              Failed balance validations will appear here
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs text-gray-500 uppercase tracking-wider">
                <th className="px-6 py-3 font-medium">Time</th>
                <th className="px-6 py-3 font-medium">File</th>
                <th className="px-6 py-3 font-medium">Bank</th>
                <th className="px-6 py-3 font-medium text-right">Expected</th>
                <th className="px-6 py-3 font-medium text-right">Actual</th>
                <th className="px-6 py-3 font-medium text-right">
                  Discrepancy
                </th>
                <th className="px-6 py-3 font-medium" />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.id}
                  className="border-b border-gray-50 hover:bg-gray-50 transition-colors"
                >
                  <td className="px-6 py-3 text-gray-500 whitespace-nowrap">
                    {new Date(item.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-3 text-gray-900 font-medium truncate max-w-[180px]">
                    {item.file_name}
                  </td>
                  <td className="px-6 py-3 text-gray-600">
                    {item.bank_detected ?? "Unknown"}
                  </td>
                  <td className="px-6 py-3 text-right text-gray-600 tabular-nums">
                    ${item.expected_ending.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-3 text-right text-gray-600 tabular-nums">
                    ${item.actual_ending.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-3 text-right text-yellow-700 font-medium tabular-nums">
                    ${item.discrepancy.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-3">
                    <button
                      onClick={() => handleRemove(item.id)}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                      title="Remove"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
