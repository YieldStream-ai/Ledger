import { FileText, CheckCircle2, AlertCircle, Loader2, X, Clock } from "lucide-react";
import { clsx } from "clsx";
import type { FileEntry } from "../../api/types";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface FileListItemProps {
  entry: FileEntry;
  isActive: boolean;
  onSelect: () => void;
  onRemove: () => void;
}

export function FileListItem({ entry, isActive, onSelect, onRemove }: FileListItemProps) {
  const statusIcon = {
    queued: <Clock className="w-3.5 h-3.5 text-gray-400" />,
    uploading: <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin" />,
    success: <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />,
    error: <AlertCircle className="w-3.5 h-3.5 text-red-500" />,
  };

  return (
    <div
      onClick={onSelect}
      className={clsx(
        "flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm group transition-colors",
        isActive
          ? "bg-blue-50 text-blue-900"
          : "hover:bg-gray-100 text-gray-700"
      )}
    >
      <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
      <span className="truncate flex-1 font-medium">{entry.file.name}</span>
      <span className="text-xs text-gray-400 flex-shrink-0">
        {formatBytes(entry.file.size)}
      </span>
      {statusIcon[entry.status]}
      {entry.status === "uploading" && (
        <span className="text-xs text-blue-500 w-8 text-right">{entry.progress}%</span>
      )}
      {entry.result?.confidence && (
        <span
          className={clsx(
            "text-xs font-medium px-1.5 py-0.5 rounded",
            entry.result.confidence.overall >= 0.7
              ? "bg-green-100 text-green-700"
              : entry.result.confidence.overall >= 0.4
                ? "bg-yellow-100 text-yellow-700"
                : "bg-red-100 text-red-700"
          )}
        >
          {Math.round(entry.result.confidence.overall * 100)}%
        </span>
      )}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
        className="opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <X className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
      </button>
    </div>
  );
}
