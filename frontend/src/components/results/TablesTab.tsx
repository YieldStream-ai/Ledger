import type { ExtractedTable } from "../../api/types";

interface TablesTabProps {
  tables: ExtractedTable[];
}

export function TablesTab({ tables }: TablesTabProps) {
  if (tables.length === 0) {
    return <p className="text-sm text-gray-500">No tables extracted.</p>;
  }

  return (
    <div className="space-y-6">
      {tables.map((table, i) => (
        <div key={i}>
          <h4 className="text-xs font-medium text-gray-500 mb-2">
            Table {i + 1} (Page {table.page})
          </h4>
          <div className="overflow-auto rounded-lg border border-gray-200">
            <table className="min-w-full text-xs">
              {table.headers.length > 0 && (
                <thead className="bg-gray-50">
                  <tr>
                    {table.headers.map((h, j) => (
                      <th
                        key={j}
                        className="px-3 py-2 text-left font-medium text-gray-700 border-b border-gray-200"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
              )}
              <tbody>
                {table.rows.map((row, ri) => (
                  <tr key={ri} className="hover:bg-gray-50">
                    {row.map((cell, ci) => (
                      <td
                        key={ci}
                        className="px-3 py-1.5 text-gray-700 border-b border-gray-100"
                      >
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
