interface EnrichmentTabProps {
  data: Record<string, unknown>;
}

function renderValue(value: unknown, depth = 0): React.ReactNode {
  if (value === null || value === undefined) {
    return <span className="text-gray-400">--</span>;
  }
  if (typeof value === "boolean") {
    return (
      <span className={value ? "text-red-600 font-medium" : "text-green-600"}>
        {value ? "Yes" : "No"}
      </span>
    );
  }
  if (typeof value === "number") {
    return <span className="font-mono">{value.toLocaleString()}</span>;
  }
  if (typeof value === "string") {
    return <span>{value}</span>;
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-gray-400">None</span>;
    return (
      <ul className="list-disc list-inside text-xs space-y-0.5">
        {value.map((item, i) => (
          <li key={i}>{renderValue(item, depth + 1)}</li>
        ))}
      </ul>
    );
  }
  if (typeof value === "object") {
    return (
      <div className={depth > 0 ? "ml-3" : ""}>
        {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
          <div key={k} className="flex gap-2 py-1 border-b border-gray-100 last:border-0">
            <span className="text-gray-500 text-xs min-w-[140px]">
              {k.replace(/_/g, " ")}
            </span>
            <span className="text-xs text-gray-900">{renderValue(v, depth + 1)}</span>
          </div>
        ))}
      </div>
    );
  }
  return <span>{String(value)}</span>;
}

export function EnrichmentTab({ data }: EnrichmentTabProps) {
  const sections = Object.entries(data);

  return (
    <div className="space-y-6">
      {sections.map(([key, value]) => (
        <div key={key} className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-900 mb-3 capitalize">
            {key.replace(/_/g, " ")}
          </h3>
          {renderValue(value)}
        </div>
      ))}
    </div>
  );
}
