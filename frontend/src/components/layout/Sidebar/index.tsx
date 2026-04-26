import { FileText, ScanSearch, FileCheck, BarChart3, ClipboardList, Layers } from "lucide-react";
import { clsx } from "clsx";
import styles from "./Sidebar.module.css";

const navItems = [
  { id: "parse", label: "Parse", icon: FileText },
  { id: "classify", label: "Classify", icon: ScanSearch },
  { id: "approval", label: "Approval", icon: FileCheck },
  { id: "enrich", label: "Enrich", icon: BarChart3 },
  { id: "templates", label: "Templates", icon: Layers },
  { id: "review", label: "Needs Review", icon: ClipboardList },
];

interface SidebarProps {
  active: string;
  onNavigate: (id: string) => void;
  healthy: boolean | null;
}

export function Sidebar({ active, onNavigate, healthy }: SidebarProps) {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>
        <h1 className={styles.title}>YieldStream</h1>
        <p className={styles.subtitle}>Qualify</p>
      </div>

      <nav className={styles.nav}>
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={clsx(
              styles.navButton,
              active === item.id && styles.navButtonActive
            )}
          >
            <item.icon className={styles.navIcon} />
            {item.label}
          </button>
        ))}
      </nav>

      <div className={styles.footer}>
        <div className={styles.statusRow}>
          <span
            className={clsx(
              styles.statusDot,
              healthy === true && styles.statusConnected,
              healthy === false && styles.statusOffline,
              healthy === null && styles.statusChecking
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
