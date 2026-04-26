import { FileListItem } from "./FileListItem";
import type { FileEntry } from "../../api/types";

interface FileListProps {
  files: FileEntry[];
  activeFileId: string | null;
  onSelect: (id: string) => void;
  onRemove: (id: string) => void;
}

export function FileList({ files, activeFileId, onSelect, onRemove }: FileListProps) {
  if (files.length === 0) return null;

  return (
    <div className="border-b border-gray-200 px-6 py-3">
      <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
        Files ({files.length})
      </h3>
      <div className="space-y-1 max-h-40 overflow-auto">
        {files.map((entry) => (
          <FileListItem
            key={entry.id}
            entry={entry}
            isActive={entry.id === activeFileId}
            onSelect={() => onSelect(entry.id)}
            onRemove={() => onRemove(entry.id)}
          />
        ))}
      </div>
    </div>
  );
}
