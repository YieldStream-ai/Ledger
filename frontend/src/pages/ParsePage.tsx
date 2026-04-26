import { useState, useCallback } from "react";
import { AppLayout } from "../components/layout/AppLayout";
import { DropZone } from "../components/upload/DropZone";
import { FileList } from "../components/upload/FileList";
import { ConfigPanel } from "../components/config/ConfigPanel";
import { TemplatesConfigPanel } from "../components/config/TemplatesConfigPanel";
import type { TemplatesSortKey } from "../components/config/TemplatesConfigPanel";
import { ResultsPanel } from "../components/results/ResultsPanel";
import { useHealthCheck } from "../hooks/useHealthCheck";
import { parseUpload } from "../api/client";
import { ReviewPage } from "./ReviewPage";
import { TemplatesPage } from "./TemplatesPage";
import type { FileEntry, ParseConfig } from "../api/types";

let nextId = 1;

export function ParsePage() {
  const healthy = useHealthCheck();
  const [activePage, setActivePage] = useState("parse");
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [activeFileId, setActiveFileId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [config, setConfig] = useState<ParseConfig>({
    documentTypeHint: "",
    includeEnrichment: false,
    crossCheckBalances: true,
    businessName: "",
    industry: "",
  });

  // Templates config state
  const [templateBankFilter, setTemplateBankFilter] = useState("");
  const [templateSortBy, setTemplateSortBy] = useState<TemplatesSortKey>("match_count");
  const [templateBankNames, setTemplateBankNames] = useState<string[]>([]);

  const handleFilesAdded = useCallback((newFiles: File[]) => {
    const entries: FileEntry[] = newFiles.map((file) => ({
      id: String(nextId++),
      file,
      status: "queued" as const,
      progress: 0,
      result: null,
      error: null,
    }));
    setFiles((prev) => [...prev, ...entries]);
    if (!activeFileId) setActiveFileId(entries[0].id);
  }, [activeFileId]);

  const handleRemove = useCallback(
    (id: string) => {
      setFiles((prev) => prev.filter((f) => f.id !== id));
      if (activeFileId === id) {
        setActiveFileId(() => {
          const remaining = files.filter((f) => f.id !== id);
          return remaining.length > 0 ? remaining[0].id : null;
        });
      }
    },
    [activeFileId, files]
  );

  const handleRunParse = useCallback(async () => {
    const queued = files.filter((f) => f.status === "queued");
    if (queued.length === 0) return;

    setIsRunning(true);

    for (const entry of queued) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === entry.id ? { ...f, status: "uploading" as const, progress: 0 } : f
        )
      );
      setActiveFileId(entry.id);

      try {
        const result = await parseUpload(entry.file, config, (pct) => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === entry.id ? { ...f, progress: pct } : f
            )
          );
        });

        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id
              ? { ...f, status: "success" as const, progress: 100, result }
              : f
          )
        );
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Unknown error";
        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id
              ? { ...f, status: "error" as const, error: message }
              : f
          )
        );
      }
    }

    setIsRunning(false);
  }, [files, config]);

  const activeFile = files.find((f) => f.id === activeFileId);
  const hasQueuedFiles = files.some((f) => f.status === "queued");

  const configPanelForRoute = (() => {
    switch (activePage) {
      case "parse":
        return (
          <ConfigPanel
            config={config}
            onChange={setConfig}
            onRunParse={handleRunParse}
            isRunning={isRunning}
            hasFiles={hasQueuedFiles}
          />
        );
      case "templates":
        return (
          <TemplatesConfigPanel
            bankFilter={templateBankFilter}
            onBankFilterChange={setTemplateBankFilter}
            bankNames={templateBankNames}
            sortBy={templateSortBy}
            onSortByChange={setTemplateSortBy}
            onRegisterNew={() => {/* TODO */}}
          />
        );
      default:
        return null;
    }
  })();

  return (
    <AppLayout
      activePage={activePage}
      onNavigate={setActivePage}
      healthy={healthy}
      configPanel={configPanelForRoute}
    >
      {activePage === "review" ? (
        <ReviewPage />
      ) : activePage === "templates" ? (
        <TemplatesPage
          bankFilter={templateBankFilter}
          sortBy={templateSortBy}
          onBankNamesLoaded={setTemplateBankNames}
        />
      ) : (
        <div className="flex flex-col h-full overflow-hidden">
          <FileList
            files={files}
            activeFileId={activeFileId}
            onSelect={setActiveFileId}
            onRemove={handleRemove}
          />

          {activeFile?.result ? (
            <div className="flex-1 overflow-auto">
              <ResultsPanel result={activeFile.result} />
            </div>
          ) : activeFile?.status === "error" ? (
            <div className="flex-1 flex items-center justify-center p-6">
              <div className="bg-red-50 text-red-700 rounded-lg p-4 max-w-md text-sm">
                <p className="font-medium">Parse failed</p>
                <p className="mt-1">{activeFile.error}</p>
              </div>
            </div>
          ) : activeFile?.status === "uploading" ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto" />
                <p className="text-sm text-gray-600 mt-4">
                  Parsing {activeFile.file.name}...
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Upload: {activeFile.progress}%
                </p>
              </div>
            </div>
          ) : (
            <div className="flex-1 min-h-0 flex p-6">
              <DropZone onFilesAdded={handleFilesAdded} />
            </div>
          )}
        </div>
      )}
    </AppLayout>
  );
}
