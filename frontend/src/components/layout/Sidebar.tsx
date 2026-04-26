import { FileText, ScanSearch, FileCheck, BarChart3, ClipboardList } from "lucide-react";
import { clsx } from "clsx";

const navItems = [
  { id: "parse", label: "Parse", icon: FileText },
  { id: "classify", label: "Classify", icon: ScanSearch },
  { id: "approval", label: "Approval", icon: FileCheck },
  { id: "enrich", label: "Enrich", icon: BarChart3 },
  { id: "review", label: "Needs Review", icon: ClipboardList },
];

interface SidebarProps {
  active: string;
  onNavigate: (id: string) => void;
  healthy: boolean | null;
}

export function Sidebar({ active, onNavigate, healthy }: SidebarProps) {
  return (
    <aside className="w-66 border-r border-gray-200 bg-gray-50 flex flex-col h-full">
      <div className="p-5 border-b border-gray-200">
        <h1 className="text-lg font-semibold text-gray-900 tracking-tight">
          YieldStream
        </h1>
        <p className="text-xs text-gray-500">Qualify</p>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={clsx(
              "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
              active === item.id
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            )}
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span
            className={clsx(
              "w-2 h-2 rounded-full",
              healthy === true && "bg-green-500",
              healthy === false && "bg-red-500",
              healthy === null && "bg-gray-400"
            )}
          />
          {healthy === true
            ? "API Connected"
            : healthy === false
              ? "API Offline"
              : "Checking..."}
        </div>
      </div>
    </aside>
  );
}
